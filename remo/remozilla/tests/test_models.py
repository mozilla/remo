from nose.tools import eq_

from remo.base.tests import RemoTestCase
from remo.profiles.tests import UserFactory
from remo.remozilla.tests import BugFactory


class ModelTest(RemoTestCase):
    """Test Bug Model."""

    def test_uppercase_status(self):
        """Test that status and resolution are always saved in uppercase."""
        mentor = UserFactory.create()
        user = UserFactory.create(userprofile__mentor=mentor)
        bug = BugFactory.create(bug_id=0000, status='foo',
                                resolution='bar', assigned_to=user)

        eq_(bug.status, 'FOO')
        eq_(bug.resolution, 'BAR')
