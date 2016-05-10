from django.contrib.auth.models import Group
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.profiles.tests import UserFactory
from remo.voting.templatetags.helpers import get_nominee, user_has_poll_permissions
from remo.voting.tests import PollFactory


class UserPollPermissionsTests(RemoTestCase):
    def test_valid_user(self):
        user = UserFactory.create(groups=['Rep'])
        group = Group.objects.get(name='Rep')
        poll = PollFactory.create(valid_groups=group)
        ok_(user_has_poll_permissions(user, poll))

    def test_invalid_user(self):
        user = UserFactory.create(groups=['Rep'])
        group = Group.objects.get(name='Mentor')
        poll = PollFactory.create(valid_groups=group)
        ok_(not user_has_poll_permissions(user, poll))

    def test_admin(self):
        user = UserFactory.create(groups=['Admin'])
        group = Group.objects.get(name='Rep')
        poll = PollFactory.create(valid_groups=group)
        ok_(user_has_poll_permissions(user, poll))


class GetNomineeProfileLink(RemoTestCase):

    def test_get_nominee_left_split(self):
        UserFactory.create(first_name='Foo foo', last_name='Bar',
                           groups=['Rep'])
        user = get_nominee('Foo foo Bar')
        ok_(user)
        eq_(user.first_name, 'Foo foo')
        eq_(user.last_name, 'Bar')

    def test_get_nominee_right_split(self):
        UserFactory.create(first_name='Foo', last_name='Foo Bar',
                           groups=['Rep'])
        user = get_nominee('Foo Foo Bar')
        ok_(user)
        eq_(user.first_name, 'Foo')
        eq_(user.last_name, 'Foo Bar')
