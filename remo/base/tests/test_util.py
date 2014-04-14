from datetime import datetime

import mock
from nose.tools import eq_

from remo.base.tests import RemoTestCase
from remo.base.utils import month2number
from remo.profiles.tests import UserFactory
from remo.reports.tests import NGReportFactory


class TestBaseUtils(RemoTestCase):
    """Tests for the utilities in base app."""

    @mock.patch('remo.base.utils.month2number', wraps=month2number)
    def test_month2number(self, mocked_month2number):
        user = UserFactory.create(groups='Rep')
        report_date = datetime(year=2014, month=4, day=1).date()
        NGReportFactory.create(user=user, report_date=report_date)
        reports_url = ('/reports/rep/' + user.userprofile.display_name +
                       '/?year=2014&month=Apri')
        response = self.client.get(reports_url, follow=True)
        mocked_month2number.assert_called_once_with(u'Apri')
        eq_(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
