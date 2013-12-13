from datetime import date, timedelta

from django.utils.timezone import now as utc_now

from nose.tools import eq_
from test_utils import TestCase
from waffle import Flag

from remo.base.tests import RemoTestCase
from remo.profiles.tests import UserFactory
from remo.reports.tests import NGReportFactory, ReportFactory
from remo.reports.utils import (get_reports_for_year, user_commited_reports,
                                REPORTS_PERMISSION_LEVEL)


class UtilsTest(TestCase):

    def setUp(self):
        """Initialize data for the tests."""
        self.mentor = UserFactory.create(username='counselor',
                                         groups=['Mentor'])
        self.user = UserFactory.create(
            username='rep', groups=['Rep'], userprofile__mentor=self.mentor,
            userprofile__date_joined_program=date(2011, 1, 1))
        ReportFactory.create(user=self.user, month=date(2012, 1, 1),
                             empty=False, overdue=True)
        ReportFactory.create(user=self.user, month=date(2012, 2, 1),
                             empty=True, overdue=False)

    def test_get_reports_anonymous(self):
        """Test get reports utility as anonymous."""
        reports = get_reports_for_year(self.user,
                                       start_year=2011,
                                       end_year=2012)

        eq_(len(reports[2011]), 12)
        for i in range(0, 12):
            eq_(reports[2011][i]['report'], None)
        eq_(len(reports[2012]), 12)
        for i in range(0, 2):
            self.assertIsNotNone(reports[2012][i]['report'])
            eq_(reports[2012][i]['class'], 'exists')
        for i in range(2, 12):
            self.assertIsNone(reports[2012][i]['report'])
            eq_(reports[2012][i]['class'], 'unavailable')

    def test_get_reports_owner(self):
        """Test get reports utility as owner."""
        reports = get_reports_for_year(
            self.user, start_year=2011, end_year=2012,
            permission=REPORTS_PERMISSION_LEVEL['owner'])

        eq_(len(reports[2011]), 12)
        eq_(len(reports[2012]), 12)
        for i in range(0, 1):
            self.assertIsNone(reports[2011][i]['report'])
            eq_(reports[2011][i]['class'], 'unavailable')
        for i in range(1, 12):
            self.assertIsNone(reports[2011][i]['report'])
            eq_(reports[2011][i]['class'], 'editable')
        for i in range(0, 2):
            self.assertIsNotNone(reports[2012][i]['report'])
            eq_(reports[2012][i]['class'], 'exists')


class TestUserCommitedReports(RemoTestCase):
    """Tests for user_commited_reports utility."""
    def setUp(self):
        Flag.objects.create(name='reports_ng_report', everyone=True)

    def test_current_streak(self):
        user = UserFactory.create()
        # Add a report every 22 hours for the last 4 days (5 reports)
        for i in range(4, 0, -1):
            NGReportFactory.create(user=user,
                                   report_date=(utc_now().date() -
                                                timedelta(days=i)))
        eq_(user_commited_reports(user, current_streak=True), 4)

    def test_longest_streak(self):
        user = UserFactory.create()
        past_day = utc_now().date() - timedelta(days=30)
        # Add 7 continuous reports somewhere in the past
        for i in range(7, 0, -1):
            NGReportFactory.create(user=user,
                                   report_date=(past_day - timedelta(days=i)))
        # Add a report, one each day for the last 4 days (5 reports)
        for i in range(6, 0, -1):
            NGReportFactory.create(user=user,
                                   report_date=(utc_now().date() -
                                                timedelta(days=i)))
        eq_(user_commited_reports(user, longest_streak=True), 7)

    def test_get_last_two_weeks_reports(self):
        user = UserFactory.create()
        # Add 4 reports more than a day apart
        for i in range(8, 0, -2):
            NGReportFactory.create(user=user,
                                   report_date=(utc_now().date() -
                                                timedelta(days=i)))
        # Get the reports added in the last two weeks
        eq_(user_commited_reports(user, period=2), 4)

    def test_get_last_ten_weeks_reports(self):
        user = UserFactory.create()
        # Add 4 reports more than a day apart
        for i in range(8, 0, -2):
            NGReportFactory.create(user=user,
                                   report_date=(utc_now().date() -
                                                timedelta(days=i)))
        # Get the reports added in the last 10 weeks
        eq_(user_commited_reports(user, period=10), 4)
