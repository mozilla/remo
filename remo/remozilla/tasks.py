import json
from datetime import datetime
from urllib import quote

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

import requests
import waffle
from celery.task import task
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

URL = ('https://api-dev.bugzilla.mozilla.org/latest/bug/'
       '?username={username}&password={password}&'
       'product=Mozilla%20Reps&component={component}&'
       'include_fields={fields}&changed_after={timedelta}d&'
       'offset={offset}&limit={limit}')

LIMIT = 100


def parse_bugzilla_time(time):
    if not time:
        return None
    datetimeobj = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
    datetimeobj = timezone.make_aware(datetimeobj, timezone.utc)
    return datetimeobj


@task
@transaction.commit_on_success
def fetch_bugs(components=COMPONENTS, days=None):
    """Fetch all bugs from Bugzilla.

    Loop over components and fetch bugs updated the last days. Link
    Bugzilla users with users on this website, when possible.

    """
    now = timezone.now()
    if not days:
        days = (now - get_last_updated_date()).days + 1

    for component in components:
        offset = 0
        url = URL.format(username=settings.REMOZILLA_USERNAME,
                         password=settings.REMOZILLA_PASSWORD,
                         component=quote(component),
                         fields=','.join(BUGZILLA_FIELDS),
                         timedelta=days, offset=offset, limit=LIMIT)

        while True:
            response = requests.get(url)
            if response.status_code != 200:
                raise ValueError('Invalid response from server.')

            bugs = json.loads(response.text)

            if not bugs['bugs']:
                break

            for bdata in bugs['bugs']:
                bug, created = Bug.objects.get_or_create(bug_id=bdata['id'])

                bug.summary = bdata.get('summary', '')
                creator_name = bdata['creator']['name']
                bug.creator = get_object_or_none(User, email=creator_name)
                bug.bug_creation_time = (
                    parse_bugzilla_time(bdata['creation_time']))
                bug.component = bdata['component']
                bug.whiteboard = bdata.get('whiteboard', '')

                bug.cc.clear()
                for person in bdata.get('cc', []):
                    cc_user = get_object_or_none(User, email=person['name'])
                    if cc_user:
                        bug.cc.add(cc_user)

                bug.assigned_to = get_object_or_none(
                    User, email=bdata['assigned_to']['name'])
                bug.status = bdata['status']
                bug.resolution = bdata.get('resolution', '')
                bug.bug_last_change_time = parse_bugzilla_time(
                    bdata.get('last_change_time'))

                for flag in bdata.get('flags', []):
                    if ((flag['status'] == '?'
                         and flag['name'] == 'remo-approval'
                         and waffle.switch_is_active('automated_polls'))):
                        bug.council_vote_requested = True

                comments = bdata.get('comments', [])
                if comments and comments[0].get('text', ''):
                    bug.first_comment = comments[0]['text']

                bug.save()

            offset += LIMIT
            url = urlparams(url, offset=offset)

    set_last_updated_date(now)
