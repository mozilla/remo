import pytz
from datetime import datetime, timedelta

from django.contrib.auth.models import Group
from django.utils.timezone import now

import factory
from factory import fuzzy

from remo.profiles.tests import UserFactory
from remo.voting.models import (Poll, PollComment, RadioPoll, RadioPollChoice,
                                RangePoll, RangePollChoice, Vote)


POLL_END_DT = now()


class PollFactory(factory.django.DjangoModelFactory):
    """Factory_Boy model for the voting_poll db table."""

    name = factory.Sequence(lambda n: 'Voting{0} example'.format(n))
    start = fuzzy.FuzzyDateTime(datetime(2011, 1, 1, tzinfo=pytz.UTC))
    end = fuzzy.FuzzyDateTime(POLL_END_DT + timedelta(days=2),
                              POLL_END_DT + timedelta(days=365 * 2))
    description = factory.Sequence(lambda n: 'This is a description {0}'.format(n))
    created_by = factory.SubFactory(UserFactory)

    class Meta:
        model = Poll

    @factory.lazy_attribute
    def valid_groups(self):
        group_names = ['Admin', 'Council', 'Mentor', 'Rep', 'Mozillians', 'Review',
                       'Peers', 'Resources', 'Onboarding']
        return Group.objects.filter(name__in=group_names).order_by('?')[0]


class VoteFactory(factory.django.DjangoModelFactory):
    """Factory_boy model for the voting_vote db table."""

    user = factory.SubFactory(UserFactory)
    poll = factory.SubFactory(PollFactory)

    class Meta:
        model = Vote


class PollWithVoteFactory(PollFactory):
    """Factory_boy model with m2m connections."""
    users_voted = factory.RelatedFactory(VoteFactory, 'poll')


class RadioPollFactory(factory.django.DjangoModelFactory):
    """Factory_Boy model for the voting_radiopoll db table."""

    question = factory.Sequence(lambda n: 'Radio Poll Question {0}'.format(n))
    poll = factory.SubFactory(PollFactory)

    class Meta:
        model = RadioPoll


class RadioPollChoiceFactory(factory.django.DjangoModelFactory):
    """Factory_Boy model for the voting_radiopollchoice db table."""

    answer = factory.Sequence(lambda n: 'Radio Poll Answer {0}'.format(n))
    votes = 0
    radio_poll = factory.SubFactory(RadioPollFactory)

    class Meta:
        model = RadioPollChoice


class RangePollFactory(factory.django.DjangoModelFactory):
    """Factory_Boy model for the voting_rangepoll db table."""

    name = factory.Sequence(lambda n: 'Range Poll {0}'.format(n))
    poll = factory.SubFactory(PollFactory)

    class Meta:
        model = RangePoll


class RangePollChoiceFactory(factory.django.DjangoModelFactory):
    """Factory_Boy model for the voting_rangepollchoice db table."""

    votes = 0
    range_poll = factory.SubFactory(RangePollFactory)
    nominee = factory.SubFactory(UserFactory)

    class Meta:
        model = RangePollChoice


class PollCommentFactory(factory.django.DjangoModelFactory):

    user = factory.SubFactory(UserFactory, userprofile__initial_council=True)
    poll = factory.SubFactory(PollFactory)
    comment = factory.Sequence(lambda n: 'Comment #{0}'.format(n))

    class Meta:
        model = PollComment
