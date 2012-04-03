import urlparse

from django.conf import settings
from jingo import register

from libravatar import libravatar_url


@register.filter
def get_avatar_url(user, size=50):
    """Get a url pointing to user's avatar.

    The libravatar network is used for avatars. Optional argument
    size can be provided to set the avatar size.

    """
    if not user:
        return None

    default_img_url = reduce(lambda u, x: urlparse.urljoin(u, x),
                             [settings.SITE_URL,
                              settings.MEDIA_URL,
                              'img/remo/remo_avatar.png'])

    return libravatar_url(email=user.email,
                          default=default_img_url,
                          size=size)
