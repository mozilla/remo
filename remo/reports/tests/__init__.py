import datetime
from random import randint

from django.db.models.signals import post_save
from django.utils.timezone import now

import factory
from factory import fuzzy

from remo.profiles.models import FunctionalArea
from remo.profiles.tests import UserFactory
from remo.reports.models import (Activity, Campaign, NGReport,
                                 NGReportComment,
                                 email_commenters_on_add_ng_report_comment)


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
    latitude = fuzzy.FuzzyDecimal(low=-90.0, high=90.0, precision=5)
    longitude = fuzzy.FuzzyDecimal(low=-180.0, high=180.0, precision=5)
    location = 'Activity Location'
    is_passive = False
    link = 'www.example.com'
    report_date = fuzzy.FuzzyDate(datetime.date(2013, 01, 01), now().date())

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
            for area in (FunctionalArea.active_objects.all()
                         .order_by('?')[:rand_int]):
                self.functional_areas.add(area)


class NGReportCommentFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = NGReportComment

    user = factory.SubFactory(UserFactory, userprofile__initial_council=True)
    report = factory.SubFactory(NGReportFactory)
    comment = factory.Sequence(lambda n: 'Comment #{0}'.format(n))


class NGReportCommentFactoryNoSignals(NGReportCommentFactory):

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        dispatch_uid = 'email_commenters_on_add_ng_report_comment_signal'
        post_save.disconnect(email_commenters_on_add_ng_report_comment,
                             NGReportComment,
                             dispatch_uid=dispatch_uid)
        comment = super(NGReportCommentFactory, cls)._create(target_class,
                                                             *args, **kwargs)
        post_save.connect(email_commenters_on_add_ng_report_comment,
                          NGReportComment,
                          dispatch_uid=dispatch_uid)
        return comment
