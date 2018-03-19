from __future__ import unicode_literals

from datetime import datetime, timedelta
from urllib import quote

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

import requests
import waffle

from remo.base.templatetags.helpers import urlparams
from remo.base.utils import get_object_or_none
from remo.celery import app
from remo.remozilla.models import Bug
from remo.remozilla.utils import get_last_updated_date, set_last_updated_date

COMPONENTS = ['Budget Requests', 'Mentorship', 'Swag Requests', 'Planning']

BUGZILLA_FIELDS = ['is_confirmed', 'summary', 'creator', 'creation_time',
                   'component', 'whiteboard', 'op_sys', 'cc', 'id',
                   'status', 'assigned_to', 'resolution',
                   'last_change_time', 'flags']

URL = ('https://bugzilla.mozilla.org/rest/bug?api_key={api_key}'
       '&product=Mozilla%20Reps&component={component}&'
       'include_fields={fields}&last_change_time={timestamp}&'
       'offset={offset}&limit={limit}')
COMMENT_URL = 'https://bugzilla.mozilla.org/rest/bug/{id}/comment?api_key={api_key}'
LIMIT = 100
BUG_WHITEBOARD = 'Review Team approval needed'
BUG_REVIEW = 'remo-review'
BUG_APPROVAL = 'remo-approval'


def parse_bugzilla_time(time):
    if not time:
        return None
    datetimeobj = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
    datetimeobj = timezone.make_aware(datetimeobj, timezone.utc)
    return datetimeobj


@app.task
@transaction.atomic
def fetch_bugs(components=COMPONENTS, days=None):
    """Fetch all bugs from Bugzilla.

    Loop over components and fetch bugs updated the last days. Link
    Bugzilla users with users on this website, when possible.

    # TODO: This can trigger a does not exist error because the task was picked
    # by the worker before the transaction was complete. Needs fixing after the
    # upgrade to a Django version > 1.8
    """
    now = timezone.now()
    if not days:
        changed_date = get_last_updated_date()
    else:
        changed_date = now - timedelta(int(days))

    for component in components:
        offset = 0
        url = URL.format(api_key=settings.REMOZILLA_API_KEY, component=quote(component),
                         fields=','.join(BUGZILLA_FIELDS),
                         timestamp=changed_date, offset=offset, limit=LIMIT)

        while True:
            bugs = requests.get(url).json()
            error = bugs.get('error')

            # Check the server response for errors
            if error:
                raise ValueError('Invalid response from server, {0}.'.format(bugs['message']))

            remo_bugs = bugs.get('bugs', [])
            if not remo_bugs:
                break

            for bdata in remo_bugs:
                # Get comments for current bug
                comment_url = COMMENT_URL.format(id=bdata['id'],
                                                 api_key=settings.REMOZILLA_API_KEY)
                comments = requests.get(comment_url).json()
                error = comments.get('error')

                if error:
                    raise ValueError('Invalid response from server, {0}.'
                                     .format(comments['message']))

                bug, created = Bug.objects.get_or_create(bug_id=bdata['id'])

                bug.summary = bdata.get('summary', '')
                creator_email = bdata['creator']
                bug.creator = get_object_or_none(User, email=creator_email)
                bug.bug_creation_time = parse_bugzilla_time(bdata['creation_time'])
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
                bug.bug_last_change_time = parse_bugzilla_time(bdata.get('last_change_time'))

                automated_voting_trigger = 0
                bug.budget_needinfo.clear()
                bug.council_member_assigned = False
                bug.pending_mentor_validation = False
                for flag in bdata.get('flags', []):
                    if flag['status'] == '?' and flag['name'] == BUG_APPROVAL:
                        automated_voting_trigger += 1
                        if BUG_WHITEBOARD in bug.whiteboard:
                            bug.council_member_assigned = True
                    if ((flag['status'] == '?' and
                         flag['name'] == 'needinfo' and 'requestee' in flag and
                         flag['requestee'] == (settings.REPS_REVIEW_ALIAS))):
                        automated_voting_trigger += 1
                    if flag['status'] == '?' and flag['name'] == BUG_REVIEW:
                        bug.pending_mentor_validation = True
                    if (flag['status'] == '?' and flag['name'] == 'needinfo' and
                            'requestee' in flag):
                        email = flag['requestee']
                        user = get_object_or_none(User, email=email)
                        if user:
                            bug.budget_needinfo.add(user)

                if automated_voting_trigger == 2 and waffle.switch_is_active('automated_polls'):
                    bug.council_vote_requested = True

                unicode_id = str(bdata['id'])
                bug_comments = comments['bugs'][unicode_id]['comments']
                if bug_comments and bug_comments[0].get('text', ''):
                    # Enforce unicode encoding.
                    bug.first_comment = bug_comments[0]['text']

                bug.save()

            offset += LIMIT
            url = urlparams(url, offset=offset)

    set_last_updated_date(now)
