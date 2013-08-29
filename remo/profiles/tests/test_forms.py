from nose.tools import ok_
from test_utils import TestCase

from remo.profiles.forms import ChangeUserForm
from remo.profiles.tests import UserFactory


class ChangeUserFormTest(TestCase):

    def setUp(self):
        self.first_user = UserFactory.create()
        self.second_user = UserFactory.create()

    def test_change_valid_bugzilla_email(self):
        """Test change bugzilla email with a valid one."""
        data = {'first_name': self.first_user.first_name,
                'last_name': self.first_user.last_name,
                'email': self.first_user.email}

        form = ChangeUserForm(data=data, instance=self.first_user)
        ok_(form.is_valid())

    def test_change_invalid_bugzilla_email(self):
        """Test change bugzilla email with an invalid one."""
        data = {'first_name': self.first_user.first_name,
                'last_name': self.first_user.last_name,
                'email': self.second_user.email}

        form = ChangeUserForm(data=data, instance=self.first_user)
        ok_(not form.is_valid())
