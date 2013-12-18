import datetime
from random import randint

from django.utils.timezone import utc

import factory
from factory import fuzzy
from product_details import product_details
from pytz import common_timezones

from remo.events.models import Event, Attendance
from remo.profiles.models import FunctionalArea
from remo.profiles.tests import UserFactory
from remo.remozilla.tests import BugFactory


COUNTRIES = product_details.get_regions('en').values()
START_DT = datetime.datetime(2011, 1, 1, tzinfo=utc)
END_DT = datetime.datetime(2011, 2, 1, tzinfo=utc)
ATTENDANCE_CHOICES = [0, 10, 50, 100, 500, 1000, 2000]


class EventFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Event

    name = factory.Sequence(lambda n: 'Event #%s' % n)
    start = fuzzy.FuzzyDateTime(START_DT, END_DT)
    end = fuzzy.FuzzyDateTime(END_DT)
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
    times_edited = fuzzy.FuzzyInteger(10)

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for category in extracted:
                self.categories.add(category)
        else:
            # create random
            rand_int = randint(1, 6)
            for area in FunctionalArea.objects.all().order_by('?')[:rand_int]:
                self.categories.add(area)


class AttendanceFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Attendance

    user = factory.SubFactory(UserFactory)
    event = factory.SubFactory(EventFactory)
    email = factory.SelfAttribute('user.email')
