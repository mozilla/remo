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

        # Check avatar db entry creation.
        ua = user.useravatar
        self.assertNotEqual(ua.avatar_url, u'', 'Avatar is empty.')

        # Check update.
        old_date = timezone.datetime(year=1970, day=1, month=1,
                                     tzinfo=timezone.utc)
        ua.last_update = old_date
        ua.save()
        get_avatar_url(user)
        self.assertGreater(ua.last_update, old_date, 'Avatar was not updated.')

        # Check caching.
        now = timezone.now()
        last_update = ua.last_update
        get_avatar_url(user)

        get_avatar_url(user)
        self.assertEqual(ua.last_update, last_update,
                         ('Avatar was updated when cached value '
                          'should have been used.'))
