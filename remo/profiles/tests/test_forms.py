from nose.tools import ok_
from test_utils import TestCase

from remo.profiles.forms import ChangeUserForm
from remo.profiles.tests import UserFactory


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
