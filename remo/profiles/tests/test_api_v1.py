import json
from datetime import datetime

from django.core.urlresolvers import reverse

import mock
from nose.tools import eq_

from remo.base.templatetags.helpers import urlparams
from remo.base.tests import RemoTestCase
from remo.profiles.tests import UserFactory


class APITest(RemoTestCase):
    """Tests profile API."""

    def test_rep_schema(self):
        """Test for valid API schema for 'rep' resource."""
        UserFactory.create(groups=['Rep'])
        url = reverse('api_get_schema', kwargs={'api_name': 'v1',
                                                'resource_name': 'rep'})
        response = self.client.get(url, follow=True)

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
        mentor = UserFactory.create(groups=['Mentor'],
                                    userprofile__initial_council=True)
        rep = UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)
        for query in [rep.email, rep.userprofile.display_name]:
            url = urlparams(reverse('api_dispatch_list',
                                    kwargs={'api_name': 'v1',
                                            'resource_name': 'rep'}),
                            query=query)
            response = self.client.get(url, follow=True)

            result = json.loads(response.content)
            eq_(len(result['objects']), 1,
                'Query "%s" did not return 1 result' % query)

    @mock.patch('remo.profiles.api.api_v1.now')
    def test_csv_export(self, fake_now):
        """Test for valid filename in CSV export."""
        # Act like it's March 2012.
        fake_now.return_value = datetime(year=2012, month=3, day=1)

        url = urlparams(reverse('api_dispatch_list',
                                kwargs={'api_name': 'v1',
                                        'resource_name': 'rep'}))

        response = self.client.get(url, data={'format': 'csv'})

        self.assertTrue('Content-Disposition' in response)
        eq_(response['Content-Disposition'],
            'filename="reps-export-2012-03-01.csv"')
