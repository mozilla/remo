import datetime

from django.contrib.auth.models import User
from nose.tools import eq_, nottest
from test_utils import TestCase

from remo.reports.models import Report


class ModelTest(TestCase):
    """Tests related to Reports Models."""
    fixtures = ['demo_users.json']

    def setUp(self):
        """Setup tests."""
        self.user = User.objects.get(username="rep")
        self.month_year = datetime.datetime(year=2012, month=1, day=10)
        self.report = Report(user=self.user, month=self.month_year)
        self.report.save()

    @nottest
    def test_mentor_set_for_new_report(self):
        """Test that report mentor field stays the same when user
        changes mentor.

        """
        eq_(self.report.mentor, self.user.userprofile.mentor)

        # Change user mentor and re-save the report. Report should
        # point to the first mentor.
        old_mentor = self.user.userprofile.mentor
        self.user.userprofile.mentor = User.objects.get(username="counselor")
        self.user.save()

        self.report.save()
        eq_(self.report.mentor, old_mentor)

    def test_overdue_true(self):
        """First test overdue auto calculation."""
        eq_(self.report.overdue, True)

    @nottest
    def test_overdue_false(self):
        """Second test overdue auto calculation."""
        # Change report created_on, so report is not overdue
        month_year = datetime.datetime(year=2020, month=1, day=10)
        report = Report(user=self.user, month=month_year)
        report.save()
        eq_(report.overdue, False)

    def test_set_month_day(self):
        """Test that reports month always points to first day of the month."""
        eq_(self.report.month.day, 1)
