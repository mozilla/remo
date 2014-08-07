from django.contrib.auth.models import Group, User
from django.core import mail
from django.utils.timezone import now

from mock import patch
from nose.tools import eq_, ok_
from test_utils import TestCase

from remo.base.utils import get_date
from remo.remozilla.tests import BugFactory
from remo.profiles.tests import UserFactory
from remo.voting.models import Poll
from remo.voting.tasks import extend_voting_period
from remo.voting.tests import (VoteFactory, PollFactoryNoSignals,
                               RadioPollChoiceFactory, RadioPollFactory)


class VotingTestTasks(TestCase):
    """Test sending notifications."""

    @patch('remo.voting.tasks.EXTEND_VOTING_PERIOD', 24 * 3600)
    def test_extend_voting_period_no_majority(self):
        bug = BugFactory.create()
        start = now().replace(microsecond=0)
        end = get_date(days=1)
        new_end = get_date(days=2)

        user = UserFactory.create(groups=['Admin'])
        group = Group.objects.get(name='Council')
        User.objects.filter(groups__name='Council').delete()
        council = UserFactory.create_batch(9, groups=['Council'])

        automated_poll = PollFactoryNoSignals.create(name='poll',
                                                     start=start, end=end,
                                                     valid_groups=group,
                                                     created_by=user,
                                                     automated_poll=True,
                                                     bug=bug)

        radio_poll = RadioPollFactory.create(poll=automated_poll,
                                             question='Budget Approval')
        RadioPollChoiceFactory.create(answer='Approved', votes=3,
                                      radio_poll=radio_poll)
        RadioPollChoiceFactory.create(answer='Denied', votes=4,
                                      radio_poll=radio_poll)
        VoteFactory.create(user=council[0], poll=automated_poll)

        extend_voting_period()

        poll = Poll.objects.get(pk=automated_poll.id)
        eq_(poll.end.year, new_end.year)
        eq_(poll.end.month, new_end.month)
        eq_(poll.end.day, new_end.day)
        eq_(poll.end.hour, 0)
        eq_(poll.end.minute, 0)
        eq_(poll.end.second, 0)
        ok_(poll.is_extended)

        reminders = map(lambda x: x.subject, mail.outbox)
        msg = '[Urgent] Voting extended for poll'

        # Test that those who voted don't receive notification
        eq_(reminders.count(msg), 8)

    @patch('remo.voting.tasks.EXTEND_VOTING_PERIOD', 24 * 3600)
    def test_extend_voting_period_majority(self):
        bug = BugFactory.create()
        start = now().replace(microsecond=0)
        end = get_date(days=1)

        user = UserFactory.create(groups=['Admin'])
        group = Group.objects.get(name='Council')
        User.objects.filter(groups__name='Council').delete()
        UserFactory.create_batch(9, groups=['Council'])

        automated_poll = PollFactoryNoSignals.create(name='poll',
                                                     start=start, end=end,
                                                     valid_groups=group,
                                                     created_by=user,
                                                     automated_poll=True,
                                                     bug=bug)

        radio_poll = RadioPollFactory.create(poll=automated_poll,
                                             question='Budget Approval')
        RadioPollChoiceFactory.create(answer='Approved', votes=5,
                                      radio_poll=radio_poll)
        RadioPollChoiceFactory.create(answer='Denied', votes=3,
                                      radio_poll=radio_poll)

        extend_voting_period()

        poll = Poll.objects.get(pk=automated_poll.id)
        eq_(poll.end.year, end.year)
        eq_(poll.end.month, end.month)
        eq_(poll.end.day, end.day)
        eq_(poll.end.hour, 0)
        eq_(poll.end.minute, 0)
        eq_(poll.end.second, 0)
        ok_(not poll.is_extended)
