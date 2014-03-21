import datetime

from django.contrib.auth.models import Group, User
from django.core import mail, management
from django.utils.timezone import now

from mock import patch
from nose.tools import eq_
from test_utils import TestCase

from remo.voting.models import Poll


class VotingTestCommands(TestCase):
    """Test sending notifications."""
    fixtures = ['demo_users.json']

    def setUp(self):
        """Initial data for the tests."""
        self.user = User.objects.get(username='admin')
        self.group = Group.objects.get(name='Council')
        self._now = now()
        self.now = self._now.replace(microsecond=0)
        self.start = self.now
        self.end = self.now + datetime.timedelta(hours=5*24)
        self.voting = Poll(name='poll', start=self.start, end=self.end,
                           valid_groups=self.group, created_by=self.user)
        self.voting.save()

    @patch('remo.voting.cron.now')
    def test_email_users_without_a_vote(self, fake_now):
        """Test sending an email to users who have not cast
        their vote yet.

        """
        # act like it's today + 1 day
        fake_now.return_value = now() + datetime.timedelta(days=1)
        args = ['poll_vote_reminder']
        management.call_command('cron', *args)
        eq_(len(mail.outbox), 3)
        for email in mail.outbox:
            eq_(email.to, ['counselor@example.com'])

    @patch('remo.voting.cron.now')
    def test_extend_voting_period_by_24hours(self, fake_now):
        """Test extending voting period by 24hours if less than
        50% of the valid users have voted and the poll ends in less than
        8 hours.

        """
        automated_poll = Poll(name='poll', start=self.start, end=self.end,
                              valid_groups=self.group, created_by=self.user,
                              automated_poll=True)
        automated_poll.save()

        # act like it's 4 hours before the end of the poll
        fake_now.return_value = now() + datetime.timedelta(hours=116)
        args = ['extend_voting_period']
        management.call_command('cron', *args)
        poll = Poll.objects.get(pk=automated_poll.id)
        eq_(poll.end - automated_poll.end, datetime.timedelta(hours=24))
