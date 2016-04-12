from datetime import datetime, timedelta

from django.db.models.signals import post_save
from django.contrib.auth.models import Group, User
from django.utils.timezone import now

from factory.django import mute_signals
from mock import patch
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.base.utils import get_date, number2month
from remo.remozilla.tests import BugFactory
from remo.profiles.tests import UserFactory
from remo.voting.models import Poll, RangePoll, RangePollChoice
from remo.voting.tasks import create_rotm_poll, extend_voting_period
from remo.voting.tests import VoteFactory, PollFactory, RadioPollChoiceFactory, RadioPollFactory


class VotingTestTasks(RemoTestCase):
    """Test sending notifications."""

    @patch('remo.voting.tasks.EXTEND_VOTING_PERIOD', 24 * 3600)
    def test_extend_voting_period_no_majority(self):
        bug = BugFactory.create()
        start = now().replace(microsecond=0)
        end = datetime.combine(get_date(days=1), datetime.min.time())
        new_end = datetime.combine(get_date(days=2), datetime.min.time())

        user = UserFactory.create(groups=['Admin'])
        group = Group.objects.get(name='Council')
        User.objects.filter(groups__name='Council').delete()
        council = UserFactory.create_batch(9, groups=['Council'])

        with mute_signals(post_save):
            automated_poll = PollFactory.create(name='poll',
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

        with patch('remo.voting.tasks.send_remo_mail.delay') as mocked_mail:
            extend_voting_period()

        poll = Poll.objects.get(pk=automated_poll.id)
        eq_(poll.end.year, new_end.year)
        eq_(poll.end.month, new_end.month)
        eq_(poll.end.day, new_end.day)
        eq_(poll.end.hour, 0)
        eq_(poll.end.minute, 0)
        eq_(poll.end.second, 0)
        ok_(poll.is_extended)

        # Test that only the 1 that hasn't voted gets a notification
        ok_(mocked_mail.called)
        eq_(mocked_mail.call_count, 1)

    @patch('remo.voting.tasks.EXTEND_VOTING_PERIOD', 24 * 3600)
    def test_extend_voting_period_majority(self):
        bug = BugFactory.create()
        start = now().replace(microsecond=0)
        end = datetime.combine(get_date(days=1), datetime.min.time())

        user = UserFactory.create(groups=['Admin'])
        group = Group.objects.get(name='Council')
        User.objects.filter(groups__name='Council').delete()
        UserFactory.create_batch(9, groups=['Council'])

        with mute_signals(post_save):
            automated_poll = PollFactory.create(name='poll',
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


class VotingRotmTestTasks(RemoTestCase):

    @patch('remo.voting.tasks.now')
    def test_base(self, mocked_now_date):
        nominee_1 = UserFactory.create(userprofile__is_rotm_nominee=True)
        nominee_2 = UserFactory.create(userprofile__is_rotm_nominee=True)
        UserFactory.create(username='remobot')
        mocked_now_date.return_value = datetime(now().year, now().month, 11)
        poll_name = ('Rep of the month for {0}'.format(
                     number2month(now().month)))

        create_rotm_poll()

        poll = Poll.objects.filter(name=poll_name)
        range_poll = RangePoll.objects.get(poll=poll)
        range_poll_choices = RangePollChoice.objects.filter(
            range_poll=range_poll)

        ok_(poll.exists())
        eq_(poll.count(), 1)
        eq_(set([choice.nominee for choice in range_poll_choices]),
            set([nominee_1, nominee_2]))

    @patch('remo.voting.tasks.waffle.switch_is_active')
    @patch('remo.voting.tasks.now')
    def test_invalid_date(self, mocked_now_date, mocked_waffle_switch):
        mocked_waffle_switch.return_value = False
        UserFactory.create(userprofile__is_rotm_nominee=True)
        UserFactory.create(userprofile__is_rotm_nominee=True)
        UserFactory.create(username='remobot')
        mocked_now_date.return_value = datetime(now().year, now().month, 5)
        poll_name = ('Rep of the month for {0}'.format(
                     number2month(now().month)))

        create_rotm_poll()

        poll = Poll.objects.filter(name=poll_name)
        ok_(not poll.exists())

    @patch('remo.voting.tasks.waffle.switch_is_active')
    @patch('remo.voting.tasks.now')
    def test_poll_already_exists(self, mocked_now_date, mocked_waffle_switch):
        mocked_waffle_switch.return_value = False
        UserFactory.create(userprofile__is_rotm_nominee=True)
        UserFactory.create(userprofile__is_rotm_nominee=True)
        UserFactory.create(username='remobot')
        # Nomination ends on the 10th of each month
        mocked_now_date.return_value = datetime(now().year, now().month, 10)
        poll_start = datetime(now().year, now().month, 1)
        poll_end = poll_start + timedelta(days=14)
        poll_name = ('Rep of the month for {0}'.format(
                     number2month(now().month)))

        mentor_group = Group.objects.get(name='Mentor')
        poll = PollFactory.create(start=poll_start,
                                  end=poll_end,
                                  valid_groups=mentor_group,
                                  name=poll_name)

        create_rotm_poll()

        rotm_polls = Poll.objects.filter(name=poll_name)
        ok_(rotm_polls.exists())
        eq_(rotm_polls.count(), 1)
        eq_(rotm_polls[0].pk, poll.pk)
