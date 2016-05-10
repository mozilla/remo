from datetime import timedelta

from django.core.urlresolvers import reverse
from django.utils.timezone import now

import mock
from nose.tools import eq_, ok_

from remo.base.templatetags.helpers import urlparams
from remo.base.tests import RemoTestCase
from remo.base.utils import month2number
from remo.profiles.tests import UserFactory
from remo.reports.tests import NGReportFactory
from remo.reports.utils import count_user_ng_reports, get_last_report


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


class Month2NumberTest(RemoTestCase):

    @mock.patch('remo.reports.views.month2number', wraps=month2number)
    def test_base(self, mocked_month2number):
        user = UserFactory.create(groups='Rep')
        reports_url = reverse('list_ng_reports_rep',
                              args=(user.userprofile.display_name,))
        reports_url = urlparams(reports_url, year='2014', month='Apri')
        response = self.client.get(reports_url, follow=True)
        mocked_month2number.assert_called_once_with(u'Apri')
        eq_(response.status_code, 404)


class GetUserLastReportTest(RemoTestCase):
    """Test get last report date helper."""

    def test_get_last_report_past(self):
        report_date = now().date() - timedelta(weeks=5)
        user = UserFactory.create(groups=['Rep'])
        NGReportFactory.create(user=user, report_date=report_date)
        eq_(get_last_report(user).report_date, report_date)

    def test_get_last_report_future(self):
        past_date = now().date() - timedelta(weeks=5)
        future_date = now().date() + timedelta(weeks=2)
        user = UserFactory.create(groups=['Rep'])
        NGReportFactory.create(user=user, report_date=past_date)
        NGReportFactory.create(user=user, report_date=future_date)
        eq_(get_last_report(user).report_date, past_date)

    def test_last_report_date_none(self):
        user = UserFactory.create(groups=['Rep'])
        ok_(not get_last_report(user))
        future_date = now().date() + timedelta(weeks=2)
        NGReportFactory.create(user=user, report_date=future_date)
        ok_(not get_last_report(user))
