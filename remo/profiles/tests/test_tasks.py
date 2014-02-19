from datetime import date
from django.contrib.auth.models import User

from nose.tools import ok_

from remo.base.tests import RemoTestCase
from remo.profiles.tasks import check_inactive_reps
from remo.profiles.tests import UserFactory
from remo.reports.tests import NGReportFactory


class InactiveUsersTest(RemoTestCase):
    def test_check_inactive(self):
        """Check for inactive reps."""
        reps = UserFactory.create_batch(3, groups=['Rep'],
                                        userprofile__inactive=False)
        check_inactive_reps.apply()
        for rep in reps:
            user = User.objects.get(id=rep.id)
            ok_(user.userprofile.inactive)

    def test_check_active(self):
        """Check for inactive reps."""
        report_date = date.today()
        reps = UserFactory.create_batch(3, groups=['Rep'],
                                        userprofile__inactive=True)
        for rep in reps:
            NGReportFactory.create(user=rep, report_date=report_date)

        check_inactive_reps.apply()
        for rep in reps:
            user = User.objects.get(id=rep.id)
            ok_(not user.userprofile.inactive)
