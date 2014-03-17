import datetime
from random import randint

from django.utils.timezone import utc

import factory
from factory import fuzzy
from product_details import product_details
from pytz import common_timezones

from remo.events.models import (Attendance, Event, EventComment, EventGoal,
                                Metric)
from remo.profiles.tests import FunctionalAreaFactory, UserFactory
from remo.remozilla.tests import BugFactory


COUNTRIES = product_details.get_regions('en').values()
START_DT = datetime.datetime(2011, 1, 1, tzinfo=utc)
END_DT = datetime.datetime(2011, 2, 1, tzinfo=utc)
ATTENDANCE_CHOICES = [10, 50, 100, 500, 1000, 2000]


class EventGoalFactory(factory.django.DjangoModelFactory):
    """Factory for FunctionalArea model."""
    FACTORY_FOR = EventGoal

    name = factory.Sequence(lambda n: 'Event goal #%s' % n)


class EventFactory(factory.django.DjangoModelFactory):
    """Factory for Event model."""
    FACTORY_FOR = Event

    name = factory.Sequence(lambda n: 'Event #%s' % n)
    start = fuzzy.FuzzyDateTime(START_DT, END_DT)
    end = fuzzy.FuzzyDateTime(END_DT + datetime.timedelta(days=3))
    timezone = fuzzy.FuzzyChoice(common_timezones)
    venue = 'VenueName'
    city = 'CityName'
    region = 'RegionName'
    country = fuzzy.FuzzyChoice(COUNTRIES)
    lat = fuzzy.FuzzyInteger(-90, 90)
    lon = fuzzy.FuzzyInteger(-180, 180)
    external_link = 'example.com'
    owner = factory.SubFactory(UserFactory)
    estimated_attendance = fuzzy.FuzzyChoice(ATTENDANCE_CHOICES)
    description = 'This is an event description.'
    extra_content = 'Extra content for event page.'
    mozilla_event = fuzzy.FuzzyChoice([True, False])
    hashtag = 'EventHashtag'
    converted_visitors = fuzzy.FuzzyInteger(100)
    swag_bug = factory.SubFactory(BugFactory)
    budget_bug = factory.SubFactory(BugFactory)
    times_edited = fuzzy.FuzzyInteger(10)

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        """Add event categories after event creation."""
        if not create:
            return
        if extracted:
            for category in extracted:
                self.categories.add(category)
        else:
            # add random number of categories
            for i in range(randint(1, 6)):
                area = FunctionalAreaFactory.create()
                self.categories.add(area)

    @factory.post_generation
    def goals(self, create, extracted, **kwargs):
        """Add event goals after event creation."""
        if not create:
            return
        if extracted:
            for goal in extracted:
                self.goals.add(goal)
        else:
            # add random number of goals
            for i in range(randint(1, 6)):
                goal = EventGoalFactory.create()
                self.goals.add(goal)

    @factory.post_generation
    def metrics(self, create, extracted, **kwargs):
        """Add event metrics after event creation."""
        if not create:
            return

        # create 2 metrics by default
        MetricFactory.create_batch(2, event=self)


class AttendanceFactory(factory.django.DjangoModelFactory):
    """Factory for Attendance model."""
    FACTORY_FOR = Attendance

    user = factory.SubFactory(UserFactory)
    event = factory.SubFactory(EventFactory)
    email = factory.SelfAttribute('user.email')


class EventCommentFactory(factory.django.DjangoModelFactory):
    """Factory for EventComment model."""
    FACTORY_FOR = EventComment

    user = factory.SubFactory(UserFactory)
    event = factory.SubFactory(EventFactory)
    comment = factory.LazyAttribute(lambda o: 'Comment for %s from %s'
                                    % (o.event, o.user))


class MetricFactory(factory.django.DjangoModelFactory):
    """Factory for Metric model."""
    FACTORY_FOR = Metric

    event = factory.SubFactory(EventFactory)
    title = factory.Sequence(lambda n: 'Event Metric #%s' % n)
    outcome = factory.Sequence(lambda n: 'Event Outcome #%s' % n)
