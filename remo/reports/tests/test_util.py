from datetime import timedelta

from django.utils.timezone import now

from nose.tools import eq_

from remo.base.tests import RemoTestCase
from remo.profiles.tests import UserFactory
from remo.reports.tests import NGReportFactory
from remo.reports.utils import count_user_ng_reports


class TestUserCommitedReports(RemoTestCase):
    """Tests for count_user_ng_reports utility."""
    def test_current_streak(self):
        user = UserFactory.create()
        # Add a report every 22 hours for the last 4 days (5 reports)
        for i in range(0, 4):
            NGReportFactory.create(user=user,
                                   report_date=(now().date() -
                                                timedelta(days=i)))
        eq_(count_user_ng_reports(user, current_streak=True), 4)

    def test_longest_streak(self):
        user = UserFactory.create()
        past_day = now().date() - timedelta(days=30)
        # Add 7 continuous reports somewhere in the past
        for i in range(0, 7):
            NGReportFactory.create(user=user,
                                   report_date=(past_day - timedelta(days=i)))

        # Add a report, one each day for the last 4 days (6 reports)
        for i in range(0, 3):
            NGReportFactory.create(user=user,
                                   report_date=(now().date() -
                                                timedelta(days=i)))
        eq_(count_user_ng_reports(user, longest_streak=True), 7)

    def test_get_last_two_weeks_reports(self):
        user = UserFactory.create()
        # Add 4 reports more than a day apart
        for i in range(8, 0, -2):
            NGReportFactory.create(user=user,
                                   report_date=(now().date() -
                                                timedelta(days=i)))
        # Get the reports added in the last two weeks
        eq_(count_user_ng_reports(user, period=2), 4)

    def test_get_last_ten_weeks_reports(self):
        user = UserFactory.create()
        # Add 4 reports more than a day apart
        for i in range(8, 0, -2):
            NGReportFactory.create(user=user,
                                   report_date=(now().date() -
                                                timedelta(days=i)))
        # Get the reports added in the last 10 weeks
        eq_(count_user_ng_reports(user, period=10), 4)
