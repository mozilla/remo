from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core import mail, management
from django.utils.timezone import now

from mock import patch
from nose.tools import eq_
from test_utils import TestCase

from remo.base.utils import get_date
from remo.remozilla.tests import BugFactory
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
        self.end = self.now + timedelta(hours=5*24)
        self.voting = Poll(name='poll', start=self.start, end=self.end,
                           valid_groups=self.group, created_by=self.user)
        self.voting.save()

    @patch('remo.voting.cron.now')
    def test_email_users_without_a_vote(self, fake_now):
        """Test sending an email to users who have not cast
        their vote yet.

        """
        # act like it's today + 1 day
        fake_now.return_value = now() + timedelta(days=1)
        args = ['poll_vote_reminder']
        management.call_command('cron', *args)
        eq_(len(mail.outbox), 3)
        eq_(mail.outbox[0].to, [u'counselor@example.com'])
        eq_(mail.outbox[1].to, [u'counselor@example.com'])
        eq_(mail.outbox[2].to, [u'Babis Sougias <counselor@example.com>'])

    @patch('remo.voting.cron.EXTEND_VOTING_PERIOD', 24 * 3600)
    def test_extend_voting_period(self):
        bug = BugFactory.create()
        end = get_date(days=1)
        new_end = get_date(days=2)

        automated_poll = Poll(name='poll', start=self.start, end=end,
                              valid_groups=self.group, created_by=self.user,
                              automated_poll=True, bug=bug)
        automated_poll.save()

        args = ['extend_voting_period']
        management.call_command('cron', *args)
        poll = Poll.objects.get(pk=automated_poll.id)
        eq_(poll.end.year, new_end.year)
        eq_(poll.end.month, new_end.month)
        eq_(poll.end.day, new_end.day)
        eq_(poll.end.hour, 0)
        eq_(poll.end.minute, 0)
        eq_(poll.end.second, 0)
