from nose.tools import eq_

from remo.base.helpers import get_country_code
from remo.base.tests import RemoTestCase


class GetCountryNameTests(RemoTestCase):
    def test_base(self):
        eq_(get_country_code('Greece'), 'gr')
        eq_(get_country_code('greece'), 'gr')

    def test_country_name_does_not_match(self):
        eq_(get_country_code('FOO'), '')
