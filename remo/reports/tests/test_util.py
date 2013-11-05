from datetime import date

from nose.tools import eq_
from test_utils import TestCase

from remo.profiles.tests import UserFactory
from remo.reports.tests import ReportFactory
from remo.reports.utils import REPORTS_PERMISSION_LEVEL, get_reports_for_year


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
