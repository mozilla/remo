from django.conf import settings
from django.contrib.auth.models import User

from nose.exc import SkipTest
from nose.tools import eq_, ok_, raises
from test_utils import TestCase
from urlparse import urlparse, parse_qs

import requests
from mock import ANY, Mock, patch

from remo.profiles.tests import UserFactory
from remo.remozilla.models import Bug
from remo.remozilla.tasks import fetch_bugs
from remo.remozilla.utils import get_last_updated_date


class FetchBugsTest(TestCase):
    fixtures = ['demo_users.json',
                'demo_bugs.json']

    @raises(requests.ConnectionError)
    @patch('requests.get')
    def test_connection_error(self, fake_get):
        """Test fetch_bugs connection error exception."""
        if ((not getattr(settings, 'REMOZILLA_USERNAME', None) or
             not getattr(settings, 'REMOZILLA_PASSWORD', None))):
            raise SkipTest('Skipping test due to unset REMOZILLA_USERNAME '
                           'or REMOZILLA_PASSWORD.')
        fake_get.side_effect = requests.ConnectionError()
        fetch_bugs()
        fake_get.assert_called_with(ANY)

    @raises(ValueError)
    @patch('remo.remozilla.tasks.requests')
    def test_invalid_return_code(self, mocked_request):
        """Test fetch_bugs invalid status code exception."""
        if ((not getattr(settings, 'REMOZILLA_USERNAME', None) or
             not getattr(settings, 'REMOZILLA_PASSWORD', None))):
            raise SkipTest('Skipping test due to unset REMOZILLA_USERNAME '
                           'or REMOZILLA_PASSWORD.')
        mocked_obj = Mock()
        mocked_request.get.return_value = mocked_obj
        mocked_response = mocked_obj
        mocked_response.json.return_value = {'error': 'Invalid login'}
        fetch_bugs()

    @patch('remo.remozilla.tasks.waffle.switch_is_active')
    @patch('remo.remozilla.tasks.requests.get')
    def test_with_valid_data(self, mocked_request, switch_is_active_mock):
        """Test fetch_bugs valid bug data processing."""
        UserFactory.create(username='remobot')
        if ((not getattr(settings, 'REMOZILLA_USERNAME', None) or
             not getattr(settings, 'REMOZILLA_PASSWORD', None))):
            raise SkipTest('Skipping test due to unset REMOZILLA_USERNAME.')

        switch_is_active_mock.return_value = True
        previous_last_updated_time = get_last_updated_date()

        mentor = UserFactory.create()
        user = UserFactory.create(groups=['Rep'], email='foo@example.com',
                                  userprofile__mentor=mentor)
        login_data = {u'token': u'bugzilla_token',
                      u'id': 12345}
        bug_data = [{'id': 7788,
                     'summary': 'This is summary',
                     'creator': 'rep@example.com',
                     'creation_time': '2010-10-5T13:45:23Z',
                     'component': 'Budget Requests',
                     'whiteboard': 'This is whiteboard',
                     'cc': ['mentor@example.com', 'not_a_rep@example.com'],
                     'assigned_to': 'mentor@example.com',
                     'status': 'resolved',
                     'flags': [{'status': '?',
                                'name': 'remo-approval'},
                               {'status': '?',
                                'name': 'needinfo',
                                'requestee': settings.REPS_COUNCIL_ALIAS},
                               {'status': '?',
                                'name': 'needinfo',
                                'requestee': 'foo@example.com'}],
                     'resolution': 'invalid'},
                    {'id': 1199,
                     'summary': 'New summary',
                     'creator': 'not_a_rep@example.com',
                     'creation_time': '2012-12-5T11:30:23Z',
                     'component': 'Budget Requests',
                     'whiteboard': 'Council Reviewer Assigned',
                     'cc': ['mentor@example.com', 'not_a_rep@example.com'],
                     'flags': [{'status': '?',
                                'name': 'remo-approval'},
                               {'status': '?',
                                'name': 'remo-review'}],
                     'assigned_to': 'mentor@example.com',
                     'status': 'resolved',
                     'resolution': 'invalid'}]

        def mocked_get(url, *args, **kwargs):
            mocked_response = Mock()

            if 'login' in url:
                mocked_response.json.return_value = login_data
                return mocked_response
            elif 'comment' in url:
                comments = {
                    'bugs': {
                        '7788': {
                            'comments': [{'text': 'foo'}, {'text': 'bar'}]
                        },
                        '1199': {
                            'comments': [{'text': 'bar'}, {'text': 'foo'}]
                        }
                    }
                }
                mocked_response.json.return_value = comments
                return mocked_response
            else:
                mocked_response.json.return_value = {'bugs': bug_data}
                url_params = parse_qs(urlparse(url).query)
                offset = url_params.get('offset')
                if offset and int(offset[0]) > 0:
                    mocked_response.json.return_value = {'bugs': []}
                return mocked_response

        mocked_request.side_effect = mocked_get
        fetch_bugs()

        eq_(Bug.objects.all().count(), 2)
        eq_(Bug.objects.filter(component='Budget Requests').count(), 2)

        # refresh status_obj
        self.assertGreater(get_last_updated_date(), previous_last_updated_time)

        bug = Bug.objects.get(bug_id=7788)
        eq_(bug.cc.all().count(), 1)
        eq_(bug.assigned_to.email, 'mentor@example.com')
        eq_(bug.resolution, 'INVALID')
        eq_(bug.creator, User.objects.get(email='rep@example.com'))
        ok_(bug.council_vote_requested)
        ok_(user in bug.budget_needinfo.all())
        eq_(bug.first_comment, 'foo')

        bug = Bug.objects.get(bug_id=1199)
        eq_(bug.creator, None)
        eq_(bug.cc.all().count(), 1)
        ok_(not bug.council_vote_requested)
        ok_(bug.pending_mentor_validation)
        ok_(bug.council_member_assigned)
        eq_(bug.first_comment, 'bar')
