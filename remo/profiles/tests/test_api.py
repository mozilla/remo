import json
from datetime import date

from django.core.urlresolvers import reverse
from django.test.client import Client
from funfactory.helpers import urlparams
from nose.tools import eq_
from test_utils import TestCase

import fudge


class APITest(TestCase):
    """Tests profile API."""
    fixtures = ['demo_users.json']

    def test_rep_schema(self):
        """Test for valid API schema for 'rep' resource."""
        c = Client()
        url = reverse('api_get_schema', kwargs={'api_name': 'v1',
                                                'resource_name': 'rep'})
        response = c.get(url, follow=True)

        result = json.loads(response.content)
        eq_(result['allowed_detail_http_methods'], ['get'],
            'Error with allowed_detail_http_methods')
        eq_(result['allowed_list_http_methods'], ['get'],
            'Error with allowed_list_http_methods')
        eq_(result['default_format'], 'application/json')
        eq_(result['fields'].keys().sort(),
            ['email', 'first_name', 'last_name', 'fullname', 'profile',
             'resource_uri'].sort())
        eq_(result['filtering']['first_name'], 1)
        eq_(result['filtering']['last_name'], 1)
        eq_(result['filtering']['profile'], 2)

    def test_rep_filter(self):
        """Test custom filtering with ?query= ."""
        c = Client()

        for query in ['rep@example', 'foci', 'koki']:
            url = urlparams(reverse('api_dispatch_list',
                                    kwargs={'api_name': 'v1',
                                            'resource_name': 'rep'}),
                            query=query)
            response = c.get(url, follow=True)

            result = json.loads(response.content)
            eq_(len(result['objects']), 1,
                'Query "%s" did not return 1 result' % query)

    @fudge.patch('datetime.date.today')
    def test_csv_export(self, fake_requests_obj):
        """Test for valid filename in CSV export."""
        # Act like it's March 2012.
        fake_date = date(year=2012, month=3, day=1)
        (fake_requests_obj.expects_call().returns(fake_date))

        c = Client()
        url = urlparams(reverse('api_dispatch_list',
                                kwargs={'api_name': 'v1',
                                        'resource_name': 'rep'}))

        response = c.get(url, data={'format': 'csv'})

        self.assertTrue('Content-Disposition' in response)
        eq_(response['Content-Disposition'],
            'filename="reps-export-2012-03-01.csv"')

    def test_rep_restricted_fields(self):
        """Test authorization to restricted fields."""
        # Unauthorized access
        c = Client()
        url = urlparams(reverse('api_dispatch_list',
                                kwargs={'api_name': 'v1',
                                        'resource_name': 'rep'}))
        response = c.get(url, follow=True)
        result = json.loads(response.content)

        for profile in result['objects']:
            self.assertFalse('email' in profile)

        # Authorized access
        c.login(username='rep', password='passwd')
        response = c.get(url, follow=True)
        result = json.loads(response.content)

        for profile in result['objects']:
            self.assertTrue('email' in profile)
