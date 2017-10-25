import datetime
from random import randint

from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User, Group
from django.utils.timezone import now, utc

import factory
from factory import fuzzy
from product_details import product_details

from remo.profiles.models import (FunctionalArea, MobilisingInterest, MobilisingSkill,
                                  UserAvatar, UserProfile,
                                  UserStatus, create_profile,
                                  email_mentor_notification,
                                  user_set_inactive_post_save)


COUNTRIES = product_details.get_regions('en').values()
START_DT = datetime.datetime(2011, 1, 1, tzinfo=utc)


class FunctionalAreaFactory(factory.django.DjangoModelFactory):
    """Factory for FunctionalArea model."""

    name = factory.Sequence(lambda n: 'Functional Area #%s' % n)

    class Meta:
        model = FunctionalArea


class MobilisingSkillFactory(factory.django.DjangoModelFactory):
    """Factory for FunctionalArea model."""

    name = factory.Sequence(lambda n: 'Mobilising Skill #%s' % n)

    class Meta:
        model = MobilisingSkill


class MobilisingInterestFactory(factory.django.DjangoModelFactory):
    """Factory for FunctionalArea model."""

    name = factory.Sequence(lambda n: 'Mobilising Interest #%s' % n)

    class Meta:
        model = MobilisingInterest


class UserProfileFactory(factory.django.DjangoModelFactory):
    """Factory for UserProfile model."""

    date_joined_program = fuzzy.FuzzyDateTime(START_DT)
    local_name = 'Local Name'
    birth_date = datetime.date(1992, 1, 1)
    city = 'User city'
    region = 'User region'
    country = fuzzy.FuzzyChoice(COUNTRIES)
    lat = fuzzy.FuzzyInteger(-90, 90)
    lon = fuzzy.FuzzyInteger(-180, 180)
    display_name = factory.Sequence(lambda n: 'UserProfile%s' % n)
    private_email = factory.Sequence(lambda n: 'personal%s@example.com' % n)
    mozillians_profile_url = 'https://mozillians.org/'
    irc_name = factory.Sequence(lambda n: 'user%s' % n)
    twitter_account = factory.Sequence(lambda n: 'user%s' % n)
    facebook_url = factory.Sequence(lambda n: 'http://facebook.com/user%s' % n)
    linkedin_url = 'http://linkedin.com/profile/'
    wiki_profile_url = 'https://wiki.mozilla.org/User:'
    gender = fuzzy.FuzzyChoice([None, True, False])
    registration_complete = True

    class Meta:
        model = UserProfile

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        dispatch_uid = 'userprofile_email_mentor_notification'
        pre_save.disconnect(email_mentor_notification, UserProfile, dispatch_uid=dispatch_uid)
        profile = super(UserProfileFactory, cls)._create(target_class, *args, **kwargs)
        pre_save.connect(email_mentor_notification, UserProfile, dispatch_uid=dispatch_uid)
        return profile

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
            for i in range(randint(1, 6)):
                area = FunctionalAreaFactory.create()
                self.functional_areas.add(area)

    @factory.post_generation
    def initial_council(self, create, extracted, **kwargs):
        """Create userprofile with self as mentor."""
        if not create:
            return
        if extracted:
            self.mentor = self.user


class UserFactory(factory.django.DjangoModelFactory):
    """User model factory."""

    username = factory.Sequence(lambda n: 'username%s' % n)
    first_name = 'John'
    last_name = factory.fuzzy.FuzzyText(length=4)
    email = factory.LazyAttribute(lambda o: '%s@example.com' % o.username)
    password = factory.PostGenerationMethodCall('set_password', 'passwd')
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = datetime.datetime(2012, 1, 1)
    date_joined = datetime.datetime(2011, 1, 1)
    userprofile = factory.RelatedFactory(UserProfileFactory, 'user')

    class Meta:
        model = User

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        post_save.disconnect(create_profile, User, dispatch_uid='create_profile_signal')
        post_save.disconnect(user_set_inactive_post_save, User,
                             dispatch_uid='user_set_inactive_post_save_signal')
        user = super(UserFactory, cls)._create(target_class, *args, **kwargs)
        post_save.connect(create_profile, User, dispatch_uid='create_profile_signal')
        post_save.connect(user_set_inactive_post_save, User,
                          dispatch_uid='user_set_inactive_post_save_signal')
        return user

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """Add list of groups to User object."""
        if not create:
            return
        if extracted:
            groups = Group.objects.filter(name__in=extracted)
            missing_groups = ([name for name in extracted
                               if name not in [group.name for group in
                                               Group.objects.all()]])
            for group_name in missing_groups:
                group = Group.objects.create(name=group_name)
            groups = Group.objects.filter(name__in=extracted)
            self.groups = groups


class UserAvatarFactory(factory.django.DjangoModelFactory):
    """Factory for UserAvatar model."""

    user = factory.SubFactory(UserFactory)
    avatar_url = 'https://example.com'

    class Meta:
        model = UserAvatar


class UserStatusFactory(factory.django.DjangoModelFactory):
    """Factory for UserStatus model."""

    user = factory.SubFactory(UserFactory)
    expected_date = fuzzy.FuzzyDate(now().date() - datetime.timedelta(weeks=1),
                                    now().date() + datetime.timedelta(weeks=1))
    is_unavailable = True

    class Meta:
        model = UserStatus
