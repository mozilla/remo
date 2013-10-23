import datetime
from random import randint

import factory
from factory import fuzzy

from remo.events.tests import EventFactory
from remo.profiles.tests import UserFactory
from remo.profiles.models import FunctionalArea
from remo.reports.models import (Report, ReportComment, ReportEvent,
                                 ReportLink, Activity, Campaign, NGReport,
                                 NGReportComment)


EMPTY_REPORT = False
FUTURE_ITEMS = 'Reports text about future items'
PAST_ITEMS = 'Reports text about past items'
FUTURE_ITEMS = 'Reports text about future items'
RECRUITS_COMMENTS = 'Comments about recruiting new contributors'
START_DT = datetime.date(2011, 1, 1)


# Factories for old reporting system

class ReportFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Report

    user = factory.SubFactory(UserFactory, userprofile__initial_council=True)
    month = fuzzy.FuzzyDate(START_DT)
    empty = EMPTY_REPORT
    recruits_comments = RECRUITS_COMMENTS
    past_items = PAST_ITEMS
    future_items = FUTURE_ITEMS


class ReportCommentFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = ReportComment

    user = factory.SubFactory(UserFactory, userprofile__initial_council=True)
    report = factory.SubFactory(ReportFactory)
    comment = factory.Sequence(lambda n: 'Comment #{0}'.format(n))


class ReportEventFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = ReportEvent

    report = factory.SubFactory(ReportFactory)
    name = factory.Sequence(lambda n: 'Event name {0}'.format(n))
    description = factory.Sequence(lambda n: 'Event {0} description'.format(n))
    link = factory.Sequence(lambda n: 'www.example.com/e/event{0}'.format(n))
    participation_type = fuzzy.FuzzyInteger(0, 2)


class ReportLinkFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = ReportLink

    report = factory.SubFactory(ReportFactory)
    description = factory.Sequence(lambda n: 'Description {0}'.format(n))
    link = factory.Sequence(lambda n: 'www.example.com/e/report{0}'.format(n))


# Factories for new reporting system

class ActivityFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Activity

    name = factory.Sequence(lambda n: 'Activity #{0}'.format(n))


class CampaignFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Campaign

    name = factory.Sequence(lambda n: 'Campaign #{0}'.format(n))


class NGReportFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = NGReport

    user = factory.SubFactory(UserFactory, userprofile__initial_council=True)
    mentor = factory.SelfAttribute('user.userprofile.mentor')
    activity = factory.SubFactory(ActivityFactory)
    campaign = factory.SubFactory(CampaignFactory)
    latitude = fuzzy.FuzzyInteger(-90, 90)
    longitude = fuzzy.FuzzyInteger(-180, 180)
    location = 'EventLocation'
    is_passive = False
    event = factory.SubFactory(EventFactory, random_categories=True)
    link = 'www.example.com'

    @factory.post_generation
    def functional_areas(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for functional_area in extracted:
                self.functional_areas.add(functional_area)

    @factory.post_generation
    def random_functional_areas(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            rand_int = randint(1, FunctionalArea.objects.count())
            for area in FunctionalArea.objects.all().order_by('?')[:rand_int]:
                self.functional_areas.add(area)


class NGReportCommentFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = NGReportComment

    user = factory.SubFactory(UserFactory, userprofile__initial_council=True)
    report = factory.SubFactory(NGReportFactory, random_functional_areas=True)
    comment = factory.Sequence(lambda n: 'Comment #{0}'.format(n))
