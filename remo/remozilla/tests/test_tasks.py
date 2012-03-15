import json

from nose.tools import eq_, raises
from test_utils import TestCase

import fudge
import requests

from remo.remozilla.models import Bug
from remo.remozilla.tasks import fetch_bugs
from remo.remozilla.utils import get_last_updated_date


class FetchBugsTest(TestCase):
    fixtures = ['demo_users.json',
                'demo_bugs.json']

    @raises(requests.ConnectionError)
    @fudge.patch('requests.get')
    def test_connection_error(self, fake_requests_obj):
        (fake_requests_obj.expects_call().raises(requests.ConnectionError))
        fetch_bugs()

    @raises(ValueError)
    @fudge.patch('requests.get')
    def test_invalid_return_code(self, fake_requests_obj):
        request = requests.Request()
        request.status_code = 500
        request.text = 'Foobar'
        (fake_requests_obj.expects_call().returns(request))
        fetch_bugs()

    @fudge.patch('requests.get')
    def test_with_valid_data(self, fake_requests_obj):
        previous_last_updated_time = get_last_updated_date()

        request = requests.Request()
        request.status_code = 200
        bug_data = {'bugs': [{'id': 7788,
                              'summary':'This is summary',
                              'creator': {'name': 'rep@example.com'},
                              'creation_time': '2010-10-5T13:45:23Z',
                              'component':'Swag Requests',
                              'whiteboard':'This is whiteboard',
                              'cc': [{'name': 'mentor@example.com'},
                                     {'name': 'not_a_rep@example.com'}],
                              'assigned_to':{'name':'mentor@example.com'},
                              'status':'resolved',
                              'resolution':'invalid',
                              'cf_due_date': None},
                             {'id': 1199,
                              'summary':'New summary',
                              'creator': {'name': 'not_a_rep@example.com'},
                              'creation_time': '2012-12-5T11:30:23Z',
                              'component':'Budget Requests',
                              'cc': [{'name': 'mentor@example.com'},
                                     {'name': 'not_a_rep@example.com'}],
                              'assigned_to':{'name':'mentor@example.com'},
                              'status':'resolved',
                              'resolution':'invalid',
                              'cf_due_date': None}]}

        request.text = json.dumps(bug_data)
        (fake_requests_obj.expects_call().returns(request))
        fetch_bugs()

        eq_(Bug.objects.all().count(), len(bug_data['bugs']))

        # refresh status_obj
        self.assertGreater(get_last_updated_date(), previous_last_updated_time)

        bug = Bug.objects.get(bug_id=7788)
        eq_(bug.cc.all().count(), 1)
        eq_(bug.assigned_to.email, 'mentor@example.com')
        eq_(bug.due_date, None)
        eq_(bug.resolution, 'INVALID')

        bug = Bug.objects.get(bug_id=1199)
        eq_(bug.creator, None)
        eq_(bug.cc.all().count(), 1)
