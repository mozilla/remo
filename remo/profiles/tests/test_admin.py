import datetime

from django.contrib.auth.models import User

import mock
from nose.tools import eq_
from test_utils import TestCase

from remo.profiles.admin import export_mentorship_csv
from remo.profiles.tests import UserFactory


class AdminTest(TestCase):
    """Test admin customizations."""

    @mock.patch('remo.profiles.admin.now')
    def test_export_mentorship_csv(self, mock_now):
        """Test mentorship csv admin action."""

        modeladmin = mock.Mock()
        request = mock.Mock()
        mock_now.return_value = datetime.datetime(2013, 11, 28, 8, 50)

        mentor = UserFactory.create(groups=['Mentor'])
        UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)
        queryset = User.objects.all()
        response = export_mentorship_csv(modeladmin, request, queryset)
        eq_(response.status_code, 200)
        attachment = 'filename="mentorship-2013-11-28-08:50.csv"'
        eq_(response['Content-Disposition'], 'attachment; %s' % attachment)
        eq_(response['Content-Type'], 'text/csv')
