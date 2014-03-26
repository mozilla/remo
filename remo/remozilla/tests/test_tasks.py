import json

from django.conf import settings
from nose.exc import SkipTest
from nose.tools import eq_, ok_, raises
from test_utils import TestCase

import requests
from mock import ANY, patch

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
    @patch('requests.get')
    def test_invalid_return_code(self, fake_get):
        """Test fetch_bugs invalid status code exception."""
        if ((not getattr(settings, 'REMOZILLA_USERNAME', None) or
             not getattr(settings, 'REMOZILLA_PASSWORD', None))):
            raise SkipTest('Skipping test due to unset REMOZILLA_USERNAME '
                           'or REMOZILLA_PASSWORD.')
        request = requests.Request()
        request.status_code = 500
        request.text = 'Foobar'
        fake_get.return_value = request
        fetch_bugs()
        fake_get.assert_called_with(ANY)

    @patch('remo.remozilla.tasks.waffle.switch_is_active')
    @patch('requests.get')
    def test_with_valid_data(self, fake_get, switch_is_active_mock):
        """Test fetch_bugs valid bug data processing."""
        UserFactory.create(username='remobot')
        if ((not getattr(settings, 'REMOZILLA_USERNAME', None) or
             not getattr(settings, 'REMOZILLA_PASSWORD', None))):
            raise SkipTest('Skipping test due to unset REMOZILLA_USERNAME.')

        switch_is_active_mock.return_value = True
        previous_last_updated_time = get_last_updated_date()

        first_request = requests.Request()
        first_request.status_code = 200
        bug_data = {'bugs': [{'id': 7788,
                              'summary': 'This is summary',
                              'creator': {'name': 'rep@example.com'},
                              'creation_time': '2010-10-5T13:45:23Z',
                              'component': 'Swag Requests',
                              'whiteboard': 'This is whiteboard',
                              'cc': [{'name': 'mentor@example.com'},
                                     {'name': 'not_a_rep@example.com'}],
                              'assigned_to': {'name': 'mentor@example.com'},
                              'status': 'resolved',
                              'flags': [
                                  {'requestee': {
                                      'ref': '',
                                      'name': 'reps-council@mozilla.com'},
                                   'status': '?',
                                   'name': 'remo-approval'}],
                              'resolution': 'invalid'},
                             {'id': 1199,
                              'summary': 'New summary',
                              'creator': {'name': 'not_a_rep@example.com'},
                              'creation_time': '2012-12-5T11:30:23Z',
                              'component': 'Swag requests',
                              'cc': [{'name': 'mentor@example.com'},
                                     {'name': 'not_a_rep@example.com'}],
                              'assigned_to': {'name': 'mentor@example.com'},
                              'status': 'resolved',
                              'resolution': 'invalid'}]}

        first_request.text = json.dumps(bug_data)

        second_request = requests.Request()
        second_request.status_code = 200
        bug_data['bugs'][0]['component'] = 'Planning'
        bug_data['bugs'][0]['id'] = 7789
        bug_data['bugs'][1]['component'] = 'Planning'
        bug_data['bugs'][1]['id'] = 1200
        second_request.text = json.dumps(bug_data)

        empty_request = requests.Request()
        empty_request.status_code = 200
        empty_request.text = json.dumps({'bugs': []})

        values = [first_request, empty_request, second_request, empty_request]
        fake_get.side_effect = values

        fetch_bugs(components=['Planning', 'Swag Requests'])

        eq_(Bug.objects.all().count(), 4)
        eq_(Bug.objects.filter(component='Planning').count(), 2)
        eq_(Bug.objects.filter(component='Swag Requests').count(), 2)

        # refresh status_obj
        self.assertGreater(get_last_updated_date(), previous_last_updated_time)

        bug = Bug.objects.get(bug_id=7788)
        eq_(bug.cc.all().count(), 1)
        eq_(bug.assigned_to.email, 'mentor@example.com')
        eq_(bug.resolution, 'INVALID')
        ok_(bug.council_vote_requested)

        bug = Bug.objects.get(bug_id=1199)
        eq_(bug.creator, None)
        eq_(bug.cc.all().count(), 1)
        ok_(not bug.council_vote_requested)
