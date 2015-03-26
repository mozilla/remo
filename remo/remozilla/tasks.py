from datetime import datetime, timedelta
from urllib import quote

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

import requests
import waffle
from celery.task import periodic_task, task
from funfactory.helpers import urlparams

from remo.base.utils import get_object_or_none
from remo.remozilla.models import Bug
from remo.remozilla.utils import get_last_updated_date, set_last_updated_date

COMPONENTS = ['Budget Requests', 'Community IT Requests', 'Mentorship',
              'Swag Requests', 'Planning']

BUGZILLA_FIELDS = [u'is_confirmed', u'summary', u'creator', u'creation_time',
                   u'component', u'whiteboard', u'op_sys', u'cc', u'id',
                   u'status', u'assigned_to', u'resolution',
                   u'last_change_time', u'flags', u'comments']

LOGIN_URL = ('https://bugzilla.mozilla.org/rest/login?login={username}'
             '&password={password}')
URL = ('https://bugzilla.mozilla.org/rest/bug?token={token}'
       '&product=Mozilla%20Reps&component={component}&'
       'include_fields={fields}&last_change_time={timestamp}&'
       'offset={offset}&limit={limit}')
LIMIT = 100


def parse_bugzilla_time(time):
    if not time:
        return None
    datetimeobj = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
    datetimeobj = timezone.make_aware(datetimeobj, timezone.utc)
    return datetimeobj


@task
def fetch_bugs(components=COMPONENTS, days=None):
    """ This task is deprecated.

    This used to run through cron on the server and it will be
    removed completely when the cron entry is removed.
    """
    return


@periodic_task(run_every=timedelta(minutes=15))
@transaction.commit_on_success
def fetch_remo_bugs(components=COMPONENTS, days=None):
    """Fetch all bugs from Bugzilla.

    Loop over components and fetch bugs updated the last days. Link
    Bugzilla users with users on this website, when possible.

    """
    login_url = LOGIN_URL.format(username=settings.REMOZILLA_USERNAME,
                                 password=settings.REMOZILLA_PASSWORD)
    response = requests.get(login_url).json()
    error = response.get('error')

    # Check the server response and get the token
    if error:
        raise ValueError('Invalid response from server, {0}.'
                         .format(response['error']))
    token = response['token']

    now = timezone.now()
    if not days:
        changed_date = get_last_updated_date()
    else:
        changed_date = now - timedelta(int(days))

    for component in components:
        offset = 0
        url = URL.format(token=token, component=quote(component),
                         fields=','.join(BUGZILLA_FIELDS),
                         timestamp=changed_date, offset=offset, limit=LIMIT)

        while True:
            bugs = requests.get(url).json()
            error = bugs.get('error')

            # Check the server response and get the token
            if error:
                raise ValueError('Invalid response from server, {0}.'
                                 .format(bugs['message']))

            remo_bugs = bugs.get('bugs', [])
            if not remo_bugs:
                break

            for bdata in remo_bugs:
                bug, created = Bug.objects.get_or_create(bug_id=bdata['id'])

                bug.summary = unicode(bdata.get('summary', ''))
                creator_email = bdata['creator']
                bug.creator = get_object_or_none(User, email=creator_email)
                bug.bug_creation_time = (
                    parse_bugzilla_time(bdata['creation_time']))
                bug.component = bdata['component']
                bug.whiteboard = bdata.get('whiteboard', '')

                bug.cc.clear()
                for email in bdata.get('cc', []):
                    cc_user = get_object_or_none(User, email=email)
                    if cc_user:
                        bug.cc.add(cc_user)

                bug.assigned_to = get_object_or_none(
                    User, email=bdata['assigned_to'])
                bug.status = bdata['status']
                bug.resolution = bdata.get('resolution', '')
                bug.bug_last_change_time = parse_bugzilla_time(
                    bdata.get('last_change_time'))

                automated_voting_trigger = 0
                bug.budget_needinfo.clear()
                bug.council_member_assigned = False
                bug.pending_mentor_validation = False
                for flag in bdata.get('flags', []):
                    if ((flag['status'] == '?' and
                         flag['name'] == 'remo-approval')):
                        automated_voting_trigger += 1
                        if 'Council Reviewer Assigned' in bug.whiteboard:
                            bug.council_member_assigned = True
                    if ((flag['status'] == '?' and
                         flag['name'] == 'needinfo' and 'requestee' in flag and
                         flag['requestee'] == (settings.REPS_COUNCIL_ALIAS))):
                        automated_voting_trigger += 1
                    if flag['status'] == '?' and flag['name'] == 'remo-review':
                        bug.pending_mentor_validation = True
                    if (flag['status'] == '?' and flag['name'] == 'needinfo'
                            and 'requestee' in flag):
                        email = flag['requestee']
                        user = get_object_or_none(User, email=email)
                        if user:
                            bug.budget_needinfo.add(user)

                if ((automated_voting_trigger == 2 and
                     waffle.switch_is_active('automated_polls'))):
                    bug.council_vote_requested = True

                comments = bdata.get('comments', [])
                if comments and comments[0].get('text', ''):
                    # Enforce unicode encoding.
                    bug.first_comment = unicode(comments[0]['text'])

                bug.save()

            offset += LIMIT
            url = urlparams(url, offset=offset)

    set_last_updated_date(now)
