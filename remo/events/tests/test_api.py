from datetime import datetime
from dateutil import parser
from mock import patch

from django.test import RequestFactory

from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.events.api.serializers import (EventDetailedSerializer,
                                         EventSerializer)
from remo.events.api.views import EventsKPIView
from remo.events.tests import EventFactory
from remo.profiles.tests import FunctionalAreaFactory, UserFactory
from remo.reports.tests import CampaignFactory


class TestEventSerializer(RemoTestCase):

    def test_base(self):
        event = EventFactory.create()
        url = '/api/beta/events/%s' % event.id
        request = RequestFactory().get(url)
        serializer = EventSerializer(event, context={'request': request})
        eq_(serializer.data['name'], event.name)
        ok_(serializer.data['_url'])


class TestEventDetailedSerializer(RemoTestCase):

    def test_base(self):
        user = UserFactory.create()
        categories = [FunctionalAreaFactory.create()]
        initiative = CampaignFactory.create()
        event = EventFactory.create(categories=categories, owner=user,
                                    campaign=initiative)
        url = '/api/beta/events/%s' % event.id
        request = RequestFactory().get(url)
        data = EventDetailedSerializer(event,
                                       context={'request': request}).data
        serialized_start = parser.parse(data['start'])
        serialized_end = parser.parse(data['end'])
        eq_(data['name'], event.name)
        eq_(data['description'], event.description)
        eq_(serialized_start.date(), event.start.date())
        eq_(serialized_start.time(), event.start.time())
        eq_(serialized_end.date(), event.end.date())
        eq_(serialized_end.time(), event.end.time())
        eq_(data['timezone'], event.timezone)
        eq_(data['city'], event.city)
        eq_(data['region'], event.region)
        eq_(data['country'], event.country)
        eq_(data['lat'], event.lat)
        eq_(data['lon'], event.lon)
        eq_(data['external_link'], event.external_link)
        eq_(data['estimated_attendance'], event.estimated_attendance)
        eq_(data['planning_pad_url'], event.planning_pad_url)
        eq_(data['hashtag'], event.hashtag)
        eq_(data['owner']['first_name'], user.first_name)
        eq_(data['owner']['last_name'], user.last_name)
        eq_(data['owner']['display_name'], user.userprofile.display_name)
        ok_(data['owner']['_url'])
        eq_(data['categories'][0]['name'], categories[0].name)
        eq_(data['initiative'], initiative.name)

    def test_get_remo_url(self):
        event = EventFactory.create()
        url = '/api/beta/events/%s' % event.id
        request = RequestFactory().get(url)
        data = EventDetailedSerializer(event,
                                       context={'request': request}).data
        ok_(event.get_absolute_url() in data['remo_url'])


class TestEventsKPIView(RemoTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = '/api/kpi/events'

    def test_total(self):
        EventFactory.create()
        request = self.factory.get(self.url)
        request.query_params = dict()
        response = EventsKPIView().get(request)
        eq_(response.data['total'], 1)

    @patch('remo.events.api.views.now')
    @patch('remo.base.utils.timezone.now')
    def test_quarter(self, mock_api_now, mock_utils_now):
        now_return_value = datetime(2015, 3, 1)
        mock_api_now.return_value = now_return_value
        mock_utils_now.return_value = now_return_value

        # Previous quarter
        start = datetime(2014, 12, 5)
        end = datetime(2014, 12, 6)
        EventFactory.create_batch(2, start=start, end=end)

        # This quarter
        start = datetime(2015, 1, 5)
        end = datetime(2015, 1, 6)
        EventFactory.create(start=start, end=end)

        # Next quarter
        start = datetime(2015, 5, 3)
        end = datetime(2015, 5, 5)
        EventFactory.create(start=start, end=end)

        request = self.factory.get(self.url)
        request.query_params = dict()

        response = EventsKPIView().get(request)
        eq_(response.data['quarter_total'], 1)
        eq_(response.data['quarter_growth_percentage'], (3-2)*100/2.0)

    @patch('remo.events.api.views.now')
    @patch('remo.base.utils.timezone.now')
    def test_current_week(self, mock_api_now, mock_utils_now):
        now_return_value = datetime(2015, 3, 1)
        mock_api_now.return_value = now_return_value
        mock_utils_now.return_value = now_return_value

        # Current week
        start = datetime(2015, 2, 25)
        end = datetime(2015, 2, 26)
        EventFactory.create(start=start, end=end)

        # Previous week
        start = datetime(2015, 2, 18)
        end = datetime(2015, 2, 19)
        EventFactory.create_batch(2, start=start, end=end)

        # Next week
        start = datetime(2015, 3, 4)
        end = datetime(2015, 3, 5)
        EventFactory.create(start=start, end=end)

        request = self.factory.get(self.url)
        request.query_params = dict()

        response = EventsKPIView().get(request)
        eq_(response.data['week_total'], 1)
        eq_(response.data['week_growth_percentage'], (1-2)*100/2.0)

    @patch('remo.events.api.views.now')
    @patch('remo.base.utils.timezone.now')
    def test_weeks(self, mock_api_now, mock_utils_now):
        now_return_value = datetime(2015, 3, 1)
        mock_api_now.return_value = now_return_value
        mock_utils_now.return_value = now_return_value

        # Current week
        start = datetime(2015, 2, 25)
        end = datetime(2015, 2, 26)
        EventFactory.create_batch(3, start=start, end=end)

        # Week-1
        start = datetime(2015, 2, 18)
        end = datetime(2015, 2, 19)
        EventFactory.create_batch(2, start=start, end=end)

        # Week-2
        start = datetime(2015, 2, 11)
        end = datetime(2015, 2, 12)
        EventFactory.create_batch(4, start=start, end=end)

        # Week-3
        start = datetime(2015, 2, 4)
        end = datetime(2015, 2, 5)
        EventFactory.create(start=start, end=end)

        # Next week
        start = datetime(2015, 3, 4)
        end = datetime(2015, 3, 5)
        EventFactory.create(start=start, end=end)

        request = self.factory.get(self.url)
        request.query_params = {'weeks': 4}

        response = EventsKPIView().get(request)
        eq_(response.data['week_total'], 3)
        eq_(response.data['week_growth_percentage'], (3-2)*100/2.0)
        total_per_week = [
            {'week': 1, 'events': 1},
            {'week': 2, 'events': 4},
            {'week': 3, 'events': 2},
            {'week': 4, 'events': 3}
        ]

        for entry in response.data['total_per_week']:
            ok_(entry in total_per_week)

        eq_(len(response.data['total_per_week']), 4)
