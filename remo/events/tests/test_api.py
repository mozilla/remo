from dateutil import parser

from django.test import RequestFactory

from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.events.api.serializers import (EventDetailedSerializer,
                                         EventSerializer)
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
