from datetime import datetime
from mock import patch

from nose.tools import eq_

from remo.base.tests import RemoTestCase
from remo.base.utils import get_quarter


class GetQuarterTest(RemoTestCase):
    def get_quarter_date(self):
        d = datetime(2015, 8, 15)
        result = get_quarter(d)
        eq_(result[0], 3)
        eq_(result[1], datetime(2015, 7, 1))

    @patch('remo.base.utils.timezone.now')
    def get_quarter_none(self, now_mock):
        now_mock.return_value = datetime(2015, 6, 15)
        result = get_quarter()
        eq_(result[0], 2)
        eq_(result[1], datetime(2015, 6, 1))
