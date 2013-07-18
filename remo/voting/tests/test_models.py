import datetime

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core import mail

import fudge

from nose.tools import eq_
from test_utils import TestCase

from remo.base.utils import datetime2pdt
from remo.profiles.tests import UserFactory
from remo.remozilla.tests import BugFactory
from remo.voting.models import Poll


class VotingMailNotificationTest(TestCase):
    """Tests related to Voting Models."""
    fixtures = ['demo_users.json']

    def setUp(self):
        """Initial data for the tests."""
        self.user = User.objects.get(username='admin')
        self.group = Group.objects.get(name='Admin')
        self._now = datetime2pdt()
        self.now = self._now.replace(microsecond=0)
        self.start = self.now
        self.end = self.now + datetime.timedelta(days=5)
        self.voting = Poll(name='poll', start=self.start, end=self.end,
                           valid_groups=self.group, created_by=self.user)
        self.voting.save()

    def test_send_email_on_save_poll(self):
        """Test sending emails when a new voting is added."""
        recipients = map(lambda x: '%s' % x.email,
                         User.objects.filter(groups=self.group))
        eq_(len(mail.outbox), 2)
        eq_(mail.outbox[0].to, recipients)
        eq_(mail.outbox[1].to, recipients)

    @fudge.patch('remo.voting.models.celery_control.revoke')
    def test_send_email_on_edit_poll(self, fake_requests_obj):
        """Test sending emails when the poll is edited."""
        Poll.objects.filter(pk=self.voting.id).update(task_start_id='1234',
                                                      task_end_id='1234')
        poll = Poll.objects.get(pk=self.voting.id)
        poll.name = 'Edit Voting'
        if not settings.CELERY_ALWAYS_EAGER:
            (fake_requests_obj.expects_call().returns(True))
        poll.save()
        eq_(len(mail.outbox), 3)


class AutomatedRadioPollTest(TestCase):
    """Tests the automatic creation of new Radio polls."""
    def setUp(self):
        """Initial data for the tests."""
        UserFactory.create(username='remobot', email='reps@mozilla.org',
                           first_name='ReMo', last_name='bot')

    def test_automated_radio_poll_valid_bug(self):
        """Test the creation of an automated radio poll."""
        bug = BugFactory.create(flag_name='remo-review', flag_status='?',
                                component='Budget Requests')
        poll = Poll.objects.get(bug=bug)
        eq_(poll.bug.bug_id, bug.bug_id)
        eq_(poll.description, bug.first_comment)
        eq_(poll.name, bug.summary)

    def test_automated_radio_poll_invalid_bug(self):
        """Test the creation of an automated radio
        poll with a non budget/swag bug.

        """
        BugFactory.create()
        eq_(Poll.objects.filter(automated_poll=True).count(), 0)

    def test_automated_radio_poll_already_exists(self):
        """Test that a radio poll is not created
        if the bug already exists.

        """
        bug = BugFactory.create(flag_name='remo-review', flag_status='?',
                                component='Budget Requests')
        bug.first_comment = 'My first comment.'
        bug.save()
        eq_(Poll.objects.filter(automated_poll=True).count(), 1)
