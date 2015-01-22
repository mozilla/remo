from datetime import datetime, timedelta

from django.conf import settings
from django.utils.timezone import now

from mock import ANY, call, patch
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.base.utils import number2month
from remo.profiles.models import UserProfile
from remo.profiles.tasks import (reset_rotm_nominees,
                                 send_rotm_nomination_reminder)
from remo.profiles.tests import UserFactory


class RotmTasksTests(RemoTestCase):

    @patch('remo.profiles.tasks.date')
    @patch('remo.profiles.tasks.now')
    def test_reset_base(self, mocked_now_date, mocked_reset_date):
        user = UserFactory.create(userprofile__is_rotm_nominee=True)
        mocked_reset_date.return_value = now().date()
        mocked_now_date.return_value = now()
        eq_(user.userprofile.is_rotm_nominee, True)

        reset_rotm_nominees()

        user_profile = UserProfile.objects.get(pk=user.userprofile.pk)
        eq_(user_profile.is_rotm_nominee, False)

    @patch('remo.profiles.tasks.date')
    @patch('remo.profiles.tasks.now')
    def test_reset_invalid_date(self, mocked_now_date, mocked_reset_date):
        user = UserFactory.create(userprofile__is_rotm_nominee=True)
        mocked_reset_date.return_value = now().date() - timedelta(days=1)
        mocked_now_date.return_value = now()
        eq_(user.userprofile.is_rotm_nominee, True)

        reset_rotm_nominees()

        user_profile = UserProfile.objects.get(pk=user.userprofile.pk)
        eq_(user_profile.is_rotm_nominee, True)

    @patch('remo.profiles.tasks.send_remo_mail')
    @patch('remo.profiles.tasks.now')
    def test_nominate_notification_base(self, mocked_date, mail_mock):
        UserFactory.create(groups=['Mentor'])
        subject = 'Nominate Rep of the month'
        mentor_alias = settings.REPS_MENTORS_LIST

        mocked_date.return_value = datetime(now().year, now().month, 1)
        send_rotm_nomination_reminder()

        ok_(mail_mock.called)
        eq_(mail_mock.call_count, 1)
        expected_call_list = [call(recipients_list=[mentor_alias],
                                   subject=subject,
                                   data={'month': number2month(now().month)},
                                   email_template=ANY)]
        eq_(mail_mock.call_args_list, expected_call_list)

    @patch('remo.profiles.tasks.send_remo_mail')
    @patch('remo.profiles.tasks.now')
    def test_nominate_notification_invalid_date(self, mocked_date, mail_mock):
        UserFactory.create(groups=['Rep'])

        send_rotm_nomination_reminder()

        ok_(not mail_mock.called)
