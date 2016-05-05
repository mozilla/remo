from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.base.utils import get_date
from remo.profiles.forms import ChangeUserForm, UserStatusForm
from remo.profiles.models import UserStatus
from remo.profiles.tests import UserFactory, UserStatusFactory


class ChangeUserFormTest(RemoTestCase):

    def test_change_valid_bugzilla_email(self):
        """Test change bugzilla email with a valid one."""
        mentor = UserFactory.create(groups=['Mentor'], userprofile__initial_council=True)
        rep = UserFactory.create(groups=['Rep'], userprofile__mentor=mentor, last_name='Doe')
        data = {'first_name': rep.first_name,
                'last_name': rep.last_name,
                'email': rep.email}

        form = ChangeUserForm(data=data, instance=rep)
        ok_(form.is_valid())

    def test_change_invalid_bugzilla_email(self):
        """Test change bugzilla email with an invalid one."""
        mentor = UserFactory.create(groups=['Mentor'], userprofile__initial_council=True)
        rep = UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)
        data = {'first_name': rep.first_name,
                'last_name': rep.last_name,
                'email': mentor.email}

        form = ChangeUserForm(data=data, instance=rep)
        ok_(not form.is_valid())


class UserStatusFormTests(RemoTestCase):
    def test_base(self):
        mentor = UserFactory.create()
        user = UserFactory.create(userprofile__mentor=mentor)
        start_date = get_date()
        expected_date = get_date(days=1)
        data = {'start_date': start_date,
                'expected_date': expected_date}
        form = UserStatusForm(data, instance=UserStatus(user=user))
        ok_(form.is_valid())
        db_obj = form.save()
        eq_(db_obj.expected_date, get_date(days=1))
        eq_(db_obj.user.get_full_name(), user.get_full_name())

    def test_invalid_expected_date(self):
        mentor = UserFactory.create()
        user = UserFactory.create(userprofile__mentor=mentor)
        start_date = get_date()
        expected_date = get_date(weeks=15)
        data = {'start_date': start_date,
                'expected_date': expected_date}
        form = UserStatusForm(data, instance=UserStatus(user=user))
        ok_(not form.is_valid())
        ok_('expected_date' in form.errors)

    def test_start_date_in_the_past(self):
        mentor = UserFactory.create()
        user = UserFactory.create(userprofile__mentor=mentor)
        start_date = get_date(-1)
        expected_date = get_date(days=2)
        data = {'start_date': start_date,
                'expected_date': expected_date}
        form = UserStatusForm(data, instance=UserStatus(user=user))
        ok_(not form.is_valid())
        ok_('start_date' in form.errors)

    def test_expected_date_before_start_date(self):
        mentor = UserFactory.create()
        user = UserFactory.create(userprofile__mentor=mentor)
        start_date = get_date(4)
        expected_date = get_date(days=2)
        data = {'start_date': start_date,
                'expected_date': expected_date}
        form = UserStatusForm(data, instance=UserStatus(user=user))
        ok_(not form.is_valid())
        ok_('expected_date' in form.errors)

    def remove_unavailability_status(self):
        mentor = UserFactory.create()
        user = UserFactory.create(userprofile__mentor=mentor)
        start_date = get_date()
        expected_date = get_date(days=1)
        data = {'start_date': start_date,
                'expected_date': expected_date}
        user_status = UserStatusFactory.create(user=user,
                                               expected_date=expected_date,
                                               start_date=start_date)
        form = UserStatusForm(data, instance=user_status)
        ok_(form.is_valid())
        ok_(not user_status.end_date)
        db_obj = form.save()
        eq_(db_obj.expected_date, get_date())
        eq_(db_obj.user.get_full_name(), user.get_full_name())
        ok_(db_obj.return_date)
