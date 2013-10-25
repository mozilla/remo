import pytz
from datetime import datetime, timedelta

from django.contrib.auth.models import Group
from django.utils.timezone import now as now_utc

import factory
from factory import fuzzy

from remo.profiles.tests import UserFactory
from remo.voting.models import (Poll, RadioPoll, RadioPollChoice, RangePoll,
                                RangePollChoice, Vote)


VALID_GROUPS = [Group.objects.get(name='Admin'),
                Group.objects.get(name='Council'),
                Group.objects.get(name='Mentor'),
                Group.objects.get(name='Rep'),
                Group.objects.get(name='Mozillians')]
POLL_END_DT = now_utc()


class PollFactory(factory.django.DjangoModelFactory):
    """Factory_Boy model for the voting_poll db table."""
    FACTORY_FOR = Poll

    name = factory.Sequence(lambda n: 'Voting{0} example'.format(n))
    start = fuzzy.FuzzyDateTime(datetime(2011, 1, 1, tzinfo=pytz.UTC))
    end = fuzzy.FuzzyDateTime(POLL_END_DT + timedelta(days=2),
                              POLL_END_DT + timedelta(days=365*2))
    valid_groups = fuzzy.FuzzyChoice(VALID_GROUPS)
    description = factory.Sequence(lambda n: ('This is a description {0}'
                                              .format(n)))
    created_by = factory.SubFactory(UserFactory)


class VoteFactory(factory.django.DjangoModelFactory):
    """Factory_boy model for the voting_vote db table."""
    FACTORY_FOR = Vote

    user = factory.SubFactory(UserFactory)
    poll = factory.SubFactory(PollFactory)


class PollWithVoteFactory(PollFactory):
    """Factory_boy model with m2m connections."""
    users_voted = factory.RelatedFactory(VoteFactory, 'poll')


class RadioPollFactory(factory.django.DjangoModelFactory):
    """Factory_Boy model for the voting_radiopoll db table."""
    FACTORY_FOR = RadioPoll

    question = factory.Sequence(lambda n: 'Radio Poll Question {0}'.format(n))
    poll = factory.SubFactory(PollFactory)


class RadioPollChoiceFactory(factory.django.DjangoModelFactory):
    """Factory_Boy model for the voting_radiopollchoice db table."""
    FACTORY_FOR = RadioPollChoice

    answer = factory.Sequence(lambda n: 'Radio Poll Answer {0}'.format(n))
    votes = 0
    radio_poll = factory.SubFactory(RadioPollFactory)


class RangePollFactory(factory.django.DjangoModelFactory):
    """Factory_Boy model for the voting_rangepoll db table."""
    FACTORY_FOR = RangePoll

    name = factory.Sequence(lambda n: 'Range Poll {0}'.format(n))
    poll = factory.SubFactory(PollFactory)


class RangePollChoiceFactory(factory.django.DjangoModelFactory):
    """Factory_Boy model for the voting_rangepollchoice db table."""
    FACTORY_FOR = RangePollChoice

    votes = 0
    range_poll = factory.SubFactory(RangePollFactory)
    nominee = factory.SubFactory(UserFactory)
