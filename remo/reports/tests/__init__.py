import datetime
from random import randint

from django.db.models.signals import post_save
from django.utils.timezone import now as now_utc

import factory
from factory import fuzzy

from remo.events.tests import EventFactory
from remo.profiles.models import FunctionalArea
from remo.profiles.tests import UserFactory
from remo.reports.models import (Report, ReportComment, ReportEvent,
                                 ReportLink, Activity, Campaign, NGReport,
                                 NGReportComment, email_mentor_on_add_report)


EMPTY_REPORT = False
FUTURE_ITEMS = 'Report text about future items'
PAST_ITEMS = 'Report text about past items'
FUTURE_ITEMS = 'Report text about future items'
RECRUITS_COMMENTS = 'Comments about recruiting new contributors'
START_DT = datetime.date(2011, 1, 1)


# Old reporting system factories
class ReportFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Report

    user = factory.SubFactory(UserFactory, userprofile__initial_council=True)
    month = fuzzy.FuzzyDate(START_DT)
    empty = EMPTY_REPORT
    recruits_comments = RECRUITS_COMMENTS
    past_items = PAST_ITEMS
    future_items = FUTURE_ITEMS


class ReportFactoryWithoutSignals(ReportFactory):

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        dispatch_uid = 'email_mentor_on_add_report_signal'
        post_save.disconnect(email_mentor_on_add_report, Report,
                             dispatch_uid=dispatch_uid)
        report = super(ReportFactory, cls)._create(target_class,
                                                   *args, **kwargs)
        post_save.connect(email_mentor_on_add_report, Report,
                          dispatch_uid=dispatch_uid)
        return report


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


# New generation reporting system factories
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
    latitude = fuzzy.FuzzyDecimal(low=-180.0, high=180.0, precision=5)
    longitude = fuzzy.FuzzyDecimal(low=-180.0, high=180.0, precision=5)
    location = 'EventLocation'
    is_passive = False
    event = factory.SubFactory(EventFactory)
    link = 'www.example.com'
    report_date = fuzzy.FuzzyDate(datetime.date(2013, 01, 01),
                                  now_utc().date())

    @factory.post_generation
    def functional_areas(self, create, extracted, **kwargs):
        """Add functional areas list after object generation."""
        if not create:
            return
        if extracted:
            for area in extracted:
                self.functional_areas.add(area)
        else:
            # create random
            rand_int = randint(1, 6)
            for area in FunctionalArea.objects.all().order_by('?')[:rand_int]:
                self.functional_areas.add(area)


class NGReportCommentFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = NGReportComment

    user = factory.SubFactory(UserFactory, userprofile__initial_council=True)
    report = factory.SubFactory(NGReportFactory)
    comment = factory.Sequence(lambda n: 'Comment #{0}'.format(n))
