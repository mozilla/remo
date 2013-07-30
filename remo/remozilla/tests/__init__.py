import datetime
from django.utils.timezone import utc

import factory
from factory import fuzzy

from remo.profiles.tests import UserFactory
from remo.remozilla.models import Bug
from remo.remozilla.tasks import COMPONENTS


CHANGE_DT = datetime.datetime(2012, 1, 1, tzinfo=utc)
CREATION_DT = datetime.datetime(2011, 1, 1, tzinfo=utc)
DUE_DT = datetime.datetime(2013, 1, 1, tzinfo=utc)
RESOLUTION = ['FIXED', 'INVALID', 'WONTFIX', 'DUPLICATE', 'WORKSFORME',
              'INCOMPLETE']
STATUS = ['UNCONFIRMED', 'NEW', 'ASSIGNED', 'REOPENED', 'READY', 'RESOLVED',
          'VERIFIED']


class BugFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Bug

    bug_id = fuzzy.FuzzyInteger(70000, 80000)
    bug_creation_time = fuzzy.FuzzyDateTime(CREATION_DT, CHANGE_DT)
    bug_last_change_time = fuzzy.FuzzyDateTime(CHANGE_DT, DUE_DT)
    creator = factory.SubFactory(UserFactory)
    assigned_to = factory.SubFactory(UserFactory)
    component = fuzzy.FuzzyChoice(COMPONENTS)
    summary = 'Bug summary'
    whiteboard = 'Bug whiteboard'
    resolution = fuzzy.FuzzyChoice(RESOLUTION)
    status = fuzzy.FuzzyChoice(STATUS)
    due_date = fuzzy.FuzzyDateTime(DUE_DT)

    @factory.post_generation
    def add_cc_users(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.cc.add(user)
