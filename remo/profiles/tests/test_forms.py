from nose.tools import eq_, ok_
from test_utils import TestCase

from remo.base.tests import RemoTestCase
from remo.base.utils import get_date
from remo.profiles.forms import ChangeUserForm, UserStatusForm
from remo.profiles.models import UserStatus
from remo.profiles.tests import UserFactory, UserStatusFactory


class ChangeUserFormTest(TestCase):

    def test_change_valid_bugzilla_email(self):
        """Test change bugzilla email with a valid one."""
        mentor = UserFactory.create(groups=['Mentor'],
                                    userprofile__initial_council=True)
        rep = UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)
        data = {'first_name': rep.first_name,
                'last_name': rep.last_name,
                'email': rep.email}

        form = ChangeUserForm(data=data, instance=rep)
        ok_(form.is_valid())

    def test_change_invalid_bugzilla_email(self):
        """Test change bugzilla email with an invalid one."""
        mentor = UserFactory.create(groups=['Mentor'],
                                    userprofile__initial_council=True)
        rep = UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)
        data = {'first_name': rep.first_name,
                'last_name': rep.last_name,
                'email': mentor.email}

        form = ChangeUserForm(data=data, instance=rep)
        ok_(not form.is_valid())


class UserStatusFormTests(RemoTestCase):
    def test_base(self):
        user = UserFactory.create()
        date = get_date()
        data = {'start_date': date}
        form = UserStatusForm(data, instance=UserStatus(user=user))
        ok_(form.is_valid())
        db_obj = form.save()
        eq_(db_obj.start_date, get_date())
        eq_(db_obj.user.get_full_name(), user.get_full_name())

    def remove_unavailability_status(self):
        user = UserFactory.create()
        date = get_date()
        data = {'start_date': date}
        user_status = UserStatusFactory.create(user=user, start_date=date)
        form = UserStatusForm(data, instance=user_status)
        ok_(form.is_valid())
        ok_(not user_status.end_date)
        db_obj = form.save()
        eq_(db_obj.start_date, get_date())
        eq_(db_obj.user.get_full_name(), user.get_full_name())
        ok_(db_obj.end_date)
