from datetime import timedelta

from django.utils.timezone import now
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.events.tests import EventFactory
from remo.profiles.models import FunctionalArea
from remo.reports import ACTIVITY_EVENT_CREATE
from remo.reports.tests import ActivityFactory


class ModelsTest(RemoTestCase):
    """Tests related to Events Models."""

    def setUp(self):
        ActivityFactory.create(name=ACTIVITY_EVENT_CREATE)
        self.event = EventFactory.create()

    def test_similar_events_category_country(self):
        """Test similar events functionality."""
        kwargs = {
            'categories': self.event.categories.all()[:1],
            'country': self.event.country,
            'start': now() + timedelta(days=10),
            'end': now() + timedelta(days=13)}

        EventFactory.create_batch(3, **kwargs)
        result = self.event.get_similar_events()
        eq_(result.count(), 3)

    def test_similar_event_country(self):
        """Test similar events functionality"""
        categories = self.event.categories.all()
        kwargs = {
            'categories': (FunctionalArea.active_objects
                           .exclude(pk__in=categories)[:4]),
            'country': self.event.country,
            'start': now() + timedelta(days=10),
            'end': now() + timedelta(days=13)}

        EventFactory.create_batch(3, **kwargs)
        result = self.event.get_similar_events()
        eq_(result.count(), 3)

    def test_similar_event_category(self):
        """Test similar events functionality"""
        kwargs = {
            'categories': self.event.categories.all()[:1],
            'country': 'CountryName',
            'start': now() + timedelta(days=10),
            'end': now() + timedelta(days=13)}

        EventFactory.create_batch(3, **kwargs)
        result = self.event.get_similar_events()
        eq_(result.count(), 3)

    def test_similar_event_no_match(self):
        """Test similar events functionality"""
        categories = self.event.categories.all()
        kwargs = {
            'categories': (FunctionalArea.active_objects
                           .exclude(pk__in=categories)[:4]),
            'country': 'CountryName',
            'start': now() + timedelta(days=10),
            'end': now() + timedelta(days=13)}

        EventFactory.create_batch(3, **kwargs)
        result = self.event.get_similar_events()
        ok_(not result.exists())
