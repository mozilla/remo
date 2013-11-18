import django.utils.timezone as timezone

from test_utils import TestCase

from remo.profiles.helpers import get_avatar_url
from remo.profiles.tests import UserFactory, UserAvatarFactory


class HelpersTest(TestCase):
    """Tests helpers."""

    def test_cached_avatar(self):
        """Test cached avatar."""
        rep = UserFactory.create(groups=['Rep'])
        UserAvatarFactory.create(user=rep)

        # Check avatar db entry creation.
        ua = rep.useravatar
        self.assertNotEqual(ua.avatar_url, u'', 'Avatar is empty.')

        # Check update.
        old_date = timezone.datetime(year=1970, day=1, month=1,
                                     tzinfo=timezone.utc)
        ua.last_update = old_date
        ua.save()
        get_avatar_url(rep)
        self.assertGreater(ua.last_update, old_date, 'Avatar was not updated.')

        # Check caching.
        last_update = ua.last_update
        get_avatar_url(rep)

        get_avatar_url(rep)
        self.assertEqual(ua.last_update, last_update,
                         ('Avatar was updated when cached value '
                          'should have been used.'))
