from datetime import timedelta

import django.utils.timezone as timezone

from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.profiles.templatetags.helpers import get_activity_level, get_avatar_url
from remo.profiles.tests import UserFactory, UserAvatarFactory
from remo.reports.tests import NGReportFactory


class HelpersTest(RemoTestCase):
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


class GetActivityLevelTest(RemoTestCase):
    """Test get_activity_level helper."""

    def test_get_activity_level_low(self):
        """Test activity level helper."""
        report_date = timezone.now().date() - timedelta(weeks=6)
        user = UserFactory.create(groups=['Rep'])
        NGReportFactory.create(user=user, report_date=report_date)
        eq_(get_activity_level(user), 'inactive-low')

    def test_get_activity_level_high(self):
        """Test activity level helper."""
        report_date = timezone.now().date() - timedelta(weeks=9)
        user = UserFactory.create(groups=['Rep'])
        NGReportFactory.create(user=user, report_date=report_date)
        eq_(get_activity_level(user), 'inactive-high')

    def test_get_activity_level_without_report(self):
        """Test activity level helper."""
        user = UserFactory.create(groups=['Rep'])
        ok_(not get_activity_level(user))
