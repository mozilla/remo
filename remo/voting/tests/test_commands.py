import datetime
import pytz

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core import mail, management
from django.utils import timezone

import fudge

from nose.tools import eq_
from test_utils import TestCase

from remo.voting.models import Poll


class VotingTestCommands(TestCase):
    """Test sending notifications."""
    fixtures = ['demo_users.json']

    def setUp(self):
        """Initial data for the tests."""
        self.user = User.objects.get(username='admin')
        self.group = Group.objects.get(name='Admin')
        self._now = timezone.make_aware(datetime.datetime.now(),
                                        pytz.timezone(settings.TIME_ZONE))
        self.now = self._now.replace(microsecond=0)
        self.start = self.now
        self.end = self.now + datetime.timedelta(days=5)
        self.voting = Poll(name='poll', start=self.start, end=self.end,
                           valid_groups=self.group, created_by=self.user)
        self.voting.save()

    @fudge.patch('remo.voting.cron.datetime.datetime.now')
    def test_email_users_without_a_vote(self, fake_requests_obj):
        """Test sending an email to users who have not cast
        their vote yet.

        """
        today = datetime.datetime.today()

        # act like it's today + 1 day
        fake_date = datetime.datetime(year=today.year, month=today.month,
                                      day=today.day + 1, hour=today.hour,
                                      minute=today.minute)
        (fake_requests_obj.expects_call().returns(fake_date))
        args = ['poll_vote_reminder']
        management.call_command('cron', *args)
        eq_(len(mail.outbox), 3)
