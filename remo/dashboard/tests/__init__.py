import datetime
from random import randint

from django.utils.timezone import now

import factory
from factory import fuzzy

from remo.dashboard.models import ActionItem
from remo.dashboard.tests.dummy_app.models import DummyModel
from remo.profiles.tests import UserFactory


class DummyModelFactory(factory.Factory):
    FACTORY_FOR = DummyModel
    name = factory.Sequence(lambda n: 'Model #{0}'.format(n))


class ActionItemFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = ActionItem

    action_type = factory.Sequence(lambda n: 'Action Item #{0}'.format(n))
    user = factory.SubFactory(UserFactory)
    due_date = fuzzy.FuzzyDate(datetime.date(2013, 01, 01), now().date())
    completed = False
    content_object = factory.SubFactory(DummyModelFactory)
    priority = randint(1, 5)
