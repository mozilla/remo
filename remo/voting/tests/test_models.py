from django.db.models.signals import post_save
from django.conf import settings

from factory.django import mute_signals
from mock import patch
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.profiles.tests import UserFactory
from remo.remozilla.tests import BugFactory
from remo.remozilla.utils import get_bugzilla_url
from remo.voting.models import Poll, automated_poll_discussion_email
from remo.voting.tests import PollCommentFactory, PollFactory


class AutomatedRadioPollTest(RemoTestCase):
    """Tests the automatic creation of new Radio polls."""
    fixtures = ['demo_users.json']

    def test_automated_radio_poll_valid_bug(self):
        """Test the creation of an automated radio poll."""
        UserFactory.create(username='remobot')
        bug = BugFactory.create(council_vote_requested=True, component='Budget Requests')
        poll = Poll.objects.get(bug=bug)
        eq_(poll.bug.bug_id, bug.bug_id)
        eq_(poll.description, bug.first_comment)
        eq_(poll.name, bug.summary)

    def test_automated_radio_poll_no_auto_bug(self):
        """Test the creation of an automated radio
        poll with a non budget/swag bug.

        """
        BugFactory.create()
        eq_(Poll.objects.filter(automated_poll=True).count(), 0)

    def test_automated_radio_poll_already_exists(self):
        """Test that a radio poll is not created
        if the bug already exists.

        """
        UserFactory.create(username='remobot')
        bug = BugFactory.create(council_vote_requested=True,
                                component='Budget Requests')
        bug.first_comment = 'My first comment.'
        bug.save()
        eq_(Poll.objects.filter(automated_poll=True).count(), 1)

    def test_send_discussion_email_to_council(self):
        bug = BugFactory.create(bug_id=989812)
        automated_poll = PollFactory.build(
            name='automated_poll', automated_poll=True, bug=bug)

        with patch('remo.voting.models.send_remo_mail') as mocked_send_mail:
            automated_poll_discussion_email(None, automated_poll, True, {})

        subject = 'Discuss [Bug 989812] - Bug summary'
        data = {'bug': bug, 'BUGZILLA_URL': get_bugzilla_url(bug),
                'poll': automated_poll}
        mocked_send_mail.delay.assert_called_once_with(
            subject=subject,
            email_template='emails/review_budget_notify_review_team.jinja',
            recipients_list=[settings.REPS_REVIEW_ALIAS],
            data=data)

    def test_send_discussion_email_to_council_edit(self):
        bug = BugFactory.create(bug_id=989812)
        automated_poll = PollFactory.build(
            name='automated_poll', automated_poll=True, bug=bug)

        with patch('remo.voting.models.send_remo_mail') as mocked_send_mail:
            automated_poll_discussion_email(None, automated_poll, False, {})

        ok_(not mocked_send_mail.called)


class VotingCommentSignalTests(RemoTestCase):

    def test_comment_one_user(self):
        """Test sending email when a new comment is added on a Poll
        and the user has the option enabled in his/her settings.
        """
        commenter = UserFactory.create()
        creator = UserFactory.create(
            userprofile__receive_email_on_add_voting_comment=True)
        # Disable notifications related to the creation of a poll
        with mute_signals(post_save):
            poll = PollFactory.create(created_by=creator)

        with patch('remo.voting.models.send_remo_mail.delay') as mail_mock:
            PollCommentFactory.create(user=commenter, poll=poll, comment='This is a comment')

        ok_(mail_mock.called)
        eq_(mail_mock.call_count, 1)

    def test_one_user_settings_False(self):
        """Test sending email when a new comment is added on a Poll
        and the user has the option disabled in his/her settings.
        """
        commenter = UserFactory.create()
        user = UserFactory.create(userprofile__receive_email_on_add_voting_comment=False)
        with mute_signals(post_save):
            poll = PollFactory.create(created_by=user)
        with patch('remo.voting.models.send_remo_mail.delay') as mail_mock:
            PollCommentFactory.create(user=commenter, poll=poll, comment='This is a comment')
        ok_(not mail_mock.called)
