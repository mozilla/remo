from django.contrib.auth.models import Group, User

from rest_framework import serializers

from remo.api.serializers import BaseKPISerializer
from remo.base.templatetags.helpers import absolutify
from remo.profiles.models import FunctionalArea, UserProfile, MobilisingInterest, MobilisingSkill


class FunctionalAreaSerializer(serializers.ModelSerializer):
    """Serializer for the FunctionalArea model."""

    class Meta:
        model = FunctionalArea
        queryset = FunctionalArea.objects.filter(active=True)
        fields = ['name']


class MobilisingSkillSerializer(serializers.ModelSerializer):
    """Serializer for the MobilisingSkill model."""

    class Meta:
        model = MobilisingSkill
        queryset = MobilisingSkill.objects.filter(active=True)
        fields = ['name']


class MobilisingInterestSerializer(serializers.ModelSerializer):
    """Serializer for the MobilisingInterest model."""

    class Meta:
        model = MobilisingInterest
        queryset = MobilisingInterest.objects.filter(active=True)
        fields = ['name']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for the django User model."""
    display_name = serializers.ReadOnlyField(source='userprofile.display_name')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'display_name', '_url']


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for the Group model."""

    class Meta:
        model = Group
        fields = ['name']


class UserProfileDetailedSerializer(serializers.HyperlinkedModelSerializer):
    """Detailed serializer for the UserProfile model."""
    first_name = serializers.ReadOnlyField(source='user.first_name')
    last_name = serializers.ReadOnlyField(source='user.last_name')
    mentor = UserSerializer()
    groups = GroupSerializer(source='user.groups', many=True)
    functional_areas = FunctionalAreaSerializer(many=True)
    mobilising_skills = MobilisingSkillSerializer(many=True)
    mobilising_interests = MobilisingInterestSerializer(many=True)
    remo_url = serializers.SerializerMethodField()
    date_joined_program = serializers.DateTimeField(format='%Y-%m-%d')
    date_left_program = serializers.DateTimeField(format='%Y-%m-%d')

    class Meta:
        model = UserProfile
        # Todo add logic for mozillians_username
        fields = ['first_name', 'last_name', 'display_name',
                  'date_joined_program', 'date_left_program', 'city', 'region',
                  'country', 'twitter_account', 'jabber_id', 'irc_name',
                  'wiki_profile_url', 'irc_channels', 'linkedin_url',
                  'facebook_url', 'diaspora_url', 'functional_areas', 'mobilising_skills',
                  'mobilising_interests', 'bio', 'mentor', 'mozillians_profile_url',
                  'timezone', 'groups', 'remo_url']

    def get_remo_url(self, obj):
        """
        Default method for fetching the profile url for the user
        in ReMo portal.
        """
        return absolutify(obj.get_absolute_url())


class PeopleKPISerializer(BaseKPISerializer):
    """Serializer for people (Reps) data."""
    inactive_week = serializers.IntegerField()
    casual_week = serializers.IntegerField()
    active_week = serializers.IntegerField()
    core_week = serializers.IntegerField()
