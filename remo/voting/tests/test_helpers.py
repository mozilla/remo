from django.contrib.auth.models import Group
from nose.tools import ok_

from remo.base.tests import RemoTestCase
from remo.profiles.tests import UserFactory
from remo.voting.helpers import user_has_poll_permissions
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
