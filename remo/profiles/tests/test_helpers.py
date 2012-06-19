from datetime import timedelta

import django.utils.timezone as timezone

from django.contrib.auth.models import User
from test_utils import TestCase

from remo.profiles.helpers import get_avatar_url


class HelpersTest(TestCase):
    """Tests helpers."""
    fixtures = ['demo_users.json']

    def test_cached_avatar(self):
        """Test cached avatar."""
        user = User.objects.get(email='rep@example.com')

        # Force avatar update
        now = timezone.now() - timedelta(seconds=1)
        get_avatar_url(user)

        ua = user.useravatar
        self.assertNotEqual(ua.avatar_url, u'', 'Avatar is empty.')
        self.assertGreater(ua.last_update, now, 'Avatar was not updated.')

        now = timezone.now()
        get_avatar_url(user)
        self.assertLess(ua.last_update, now,
                        ('Avatar was updated when cached value '
                         'should have been used.'))
