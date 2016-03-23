import urlparse

from datetime import timedelta

from django.utils import timezone

from django.conf import settings
from jingo import register

import urllib2
import json

from remo.profiles.models import FunctionalArea, UserAvatar
from remo.reports.utils import get_last_report


INACTIVE_HIGH = timedelta(weeks=8)
INACTIVE_LOW = timedelta(weeks=4)


@register.filter
def get_avatar_url(user, size=50):
    """Get a url pointing to user's avatar.

    The libravatar network is used for avatars. Return cached value if
    its last update was less than 24 hours before. Optional argument
    size can be provided to set the avatar size.

    """
    if not user:
        return None

    user_avatar, created = UserAvatar.objects.get_or_create(user=user)
    now = timezone.now()
    avatar_url = ''

    if (user_avatar.last_update < now - timedelta(days=7)) or created:
        # Get the user id
        ask_json = '&format=json'
        user_url = 'https://mozillians.org/api/v2/users?api-key='
        user_url = user_url + settings.MOZILLIANS_KEY
        req = urllib2.Request(user_url + '&email=' + user.email + ask_json)
        opener = urllib2.build_opener()
        f = opener.open(req)
        response = json.loads(f.read())
        f.close()
        if response['count'] > 0:
            user_url = response['results'][0]['_url']
            user_url = user_url + '?api-key=' + settings.MOZILLIANS_KEY
            req_avatar = urllib2.Request(user_url + ask_json)
            opener = urllib2.build_opener()
            f_avatar = opener.open(req_avatar)
            response_avatar = json.loads(f_avatar.read())
            f_avatar.close()
            user_avatar.avatar_url = response_avatar['photo']['150x150']
            avatar_url = user_avatar.avatar_url
            user_avatar.save()
        else:
            avatar_url = reduce(lambda u, x: urlparse.urljoin(u, x),
                                [settings.SITE_URL,
                                 settings.STATIC_URL,
                                 'base/img/remo/remo_avatar.png'])

    if size != -1:
        # TODO resize the image
        pass

    return avatar_url


@register.filter
def get_functional_area(name):
    """Return the Functional Area object given the name."""
    try:
        return FunctionalArea.objects.get(name=name)
    except FunctionalArea.DoesNotExist:
        return None


@register.filter
def get_activity_level(user):
    """Return user's inactivity level."""
    last_report = get_last_report(user)
    if not last_report:
        return ''

    today = timezone.now().date()
    inactivity_period = today - last_report.report_date

    if inactivity_period > INACTIVE_LOW:
        if inactivity_period > INACTIVE_HIGH:
            return 'inactive-high'
        return 'inactive-low'
    return ''
