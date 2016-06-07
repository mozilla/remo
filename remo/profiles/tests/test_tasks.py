from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import now

from mock import ANY, call, patch
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.base.utils import number2month
from remo.profiles.models import UserProfile, UserStatus
from remo.profiles.tasks import (check_mozillian_username, reset_rotm_nominees,
                                 send_rotm_nomination_reminder, set_unavailability_flag)
from remo.profiles.tests import UserFactory, UserStatusFactory
from remo.base.utils import get_date


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


class UserStatusTests(RemoTestCase):

    def test_base(self):
        mentor = UserFactory.create()
        rep = UserFactory.create(userprofile__mentor=mentor)
        UserStatusFactory.create(user=rep, start_date=get_date(days=-1),
                                 is_unavailable=False)
        set_unavailability_flag()
        status = UserStatus.objects.get(user=rep)
        ok_(status.is_unavailable)


class MozillianUsernameTests(RemoTestCase):

    @patch('remo.profiles.tasks.is_vouched')
    def test_mozillian_username_length(self, mocked_vouch_status):
        mozillian = UserFactory.create(first_name='Awesome', last_name='Mozillian',
                                       groups=['Mozillians'])
        mocked_vouch_status.return_value = {'is_vouched': True,
                                            'username': 'foobar',
                                            'full_name': ('A really really long name for our '
                                                          ' Awesome Mozillian')}
        check_mozillian_username()
        mozillian = User.objects.get(id=mozillian.id)
        eq_(mozillian.first_name, 'A')
        eq_(mozillian.last_name, 'really really long name for ou')
