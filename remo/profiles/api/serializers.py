from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse

from rest_framework import serializers

from remo.base.helpers import absolutify
from remo.profiles.models import FunctionalArea, UserProfile


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for the Group model."""

    class Meta:
        model = Group
        fields = ['name']


class FunctionalAreaSerializer(serializers.ModelSerializer):
    """Serializer for the FunctionalArea model."""

    class Meta:
        model = FunctionalArea
        fields = ['name']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for the django User model."""

    display_name = serializers.ReadOnlyField(source='userprofile.display_name')
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'display_name', 'email',
                  'profile_url', '_url']

    def get_profile_url(self, obj):
        """
        Default method for fetching the profile url for the user
        in ReMo portal.
        """
        url = reverse('remo.profiles.views.view_profile',
                      kwargs={'display_name': obj.userprofile.display_name})
        return absolutify(url)


class UserProfileDetailedSerializer(serializers.HyperlinkedModelSerializer):
    """Detailed serializer for the UserProfile model."""

    mentor = UserSerializer()
    groups = GroupSerializer(source='user.groups', many=True)
    functional_areas = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        # Todo add logic for mozillians_username
        fields = ['display_name', 'date_joined_program', 'date_left_program',
                  'city', 'region', 'country', 'twitter_account', 'jabber_id',
                  'irc_name', 'wiki_profile_url', 'irc_channels',
                  'linkedin_url', 'facebook_url', 'diaspora_url',
                  'functional_areas', 'bio', 'mentor',
                  'mozillians_profile_url', 'timezone', 'groups']

    def get_functional_areas(self, profile):
        """Get the active functional areas for each user."""
        items = profile.functional_areas.filter(active=True)
        serializer = FunctionalAreaSerializer(instance=items, many=True)
        return serializer.data
