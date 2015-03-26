from rest_framework import serializers

from remo.base.helpers import absolutify
from remo.events.models import Event
from remo.profiles.api.serializers import (FunctionalAreaSerializer,
                                           UserSerializer)


class EventSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for the Event model."""

    class Meta:
        model = Event
        fields = ['name', '_url']


class EventDetailedSerializer(serializers.HyperlinkedModelSerializer):
    """Detailed serializer for the Event model."""
    categories = FunctionalAreaSerializer(many=True)
    owner = UserSerializer()
    remo_url = serializers.SerializerMethodField()
    initiative = serializers.ReadOnlyField(source='campaign.name')

    class Meta:
        model = Event
        fields = ['name', 'description', 'start', 'end', 'timezone', 'city',
                  'region', 'country', 'lat', 'lon', 'owner', 'external_link',
                  'initiative', 'categories', 'estimated_attendance',
                  'planning_pad_url', 'hashtag', 'remo_url']

    def get_remo_url(self, obj):
        """
        Default method for fetching the url for the event
        in ReMo portal.
        """
        return absolutify(obj.get_absolute_url())


class EventsKPISerializer(serializers.Serializer):
    """Serializer for the Events KPI data"""
    total = serializers.IntegerField()
    total_quarter = serializers.IntegerField()
    percentage_quarter = serializers.FloatField()
    total_week = serializers.IntegerField()
    percentage_week = serializers.FloatField()
    total_per_week = serializers.ListField()
