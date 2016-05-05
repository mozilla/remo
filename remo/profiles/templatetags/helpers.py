import urlparse

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from django_jinja import library
from libravatar import libravatar_url

from remo.base.templatetags.helpers import urlparams
from remo.profiles.models import FunctionalArea, UserAvatar
from remo.reports.utils import get_last_report


INACTIVE_HIGH = timedelta(weeks=8)
INACTIVE_LOW = timedelta(weeks=4)


@library.filter
def get_avatar_url(user, size=50):
    """Get a url pointing to user's avatar.

    The libravatar network is used for avatars. Return cached value if
    its last update was less than 24 hours before. Optional argument
    size can be provided to set the avatar size.

    """
    if not user:
        return None

    default_img_url = reduce(lambda u, x: urlparse.urljoin(u, x),
                             [settings.SITE_URL,
                              settings.STATIC_URL,
                              'base/img/remo/remo_avatar.png'])

    user_avatar, created = UserAvatar.objects.get_or_create(user=user)
    now = timezone.now()

    if (user_avatar.last_update < now - timedelta(days=7)) or created:
        user_avatar.avatar_url = libravatar_url(email=user.email, https=True)
        user_avatar.save()

    avatar_url = urlparams(user_avatar.avatar_url, default=default_img_url)
    if size != -1:
        avatar_url = urlparams(avatar_url, size=size)

    return avatar_url


@library.filter
def get_functional_area(name):
    """Return the Functional Area object given the name."""
    try:
        return FunctionalArea.objects.get(name=name)
    except FunctionalArea.DoesNotExist:
        return None


@library.filter
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
