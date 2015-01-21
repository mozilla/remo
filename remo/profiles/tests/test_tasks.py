from datetime import timedelta

from django.utils.timezone import now

from mock import patch
from nose.tools import eq_

from remo.base.tests import RemoTestCase
from remo.profiles.models import UserProfile
from remo.profiles.tasks import reset_rotm_nominees
from remo.profiles.tests import UserFactory


class RotmTasksTests(RemoTestCase):

    @patch('remo.profiles.tasks.date')
    @patch('remo.profiles.tasks.now')
    def test_base(self, mocked_now_date, mocked_reset_date):
        user = UserFactory.create(userprofile__is_rotm_nominee=True)
        mocked_reset_date.return_value = now().date()
        mocked_now_date.return_value = now()
        eq_(user.userprofile.is_rotm_nominee, True)

        reset_rotm_nominees()

        user_profile = UserProfile.objects.get(pk=user.userprofile.pk)
        eq_(user_profile.is_rotm_nominee, False)

    @patch('remo.profiles.tasks.date')
    @patch('remo.profiles.tasks.now')
    def test_invalid_date(self, mocked_now_date, mocked_reset_date):
        user = UserFactory.create(userprofile__is_rotm_nominee=True)
        mocked_reset_date.return_value = now().date() - timedelta(days=1)
        mocked_now_date.return_value = now()
        eq_(user.userprofile.is_rotm_nominee, True)

        reset_rotm_nominees()

        user_profile = UserProfile.objects.get(pk=user.userprofile.pk)
        eq_(user_profile.is_rotm_nominee, True)
