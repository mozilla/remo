from nose.tools import eq_
from test_utils import TestCase

from remo.remozilla.models import Bug


class ModelTest(TestCase):
    """Test Bug Model."""

    def test_uppercase_status(self):
        """Test that status and resolution are always saved in uppercase."""
        bug = Bug(bug_id=0000, status="foo", resolution="bar")
        bug.save()

        eq_(bug.status, "FOO")
        eq_(bug.resolution, "BAR")
