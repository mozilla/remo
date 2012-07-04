import json

from django.core.urlresolvers import reverse
from django.test.client import Client
from funfactory.helpers import urlparams
from nose.tools import eq_
from test_utils import TestCase


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
