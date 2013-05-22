import datetime
import pytz

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core import mail
from django.utils import timezone

import fudge

from nose.tools import eq_
from test_utils import TestCase

from remo.voting.models import Poll


class VotingMailNotificationTest(TestCase):
    """Tests related to Voting Models."""
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

    def test_send_email_on_save_poll(self):
        """Test sending emails when a new voting is added."""
        eq_(len(mail.outbox), 2)

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
