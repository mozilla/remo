from rest_framework import serializers

from remo.base.helpers import absolutify
from remo.events.models import Event
from remo.profiles.api.serializers import (FunctionalAreaSerializer,
                                           UserSerializer)


class EventSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for the Event model."""

    event_url = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['name', 'event_url', '_url']

    def get_event_url(self, obj):
        """
        Default method for fetching the url for the event
        in ReMo portal.
        """
        return absolutify(obj.get_absolute_url())


class EventDetailedSerializer(serializers.HyperlinkedModelSerializer):
    """Detailed serializer for the Event model."""

    functional_areas = serializers.SerializerMethodField()
    owner = UserSerializer()

    class Meta:
        model = Event
        fields = ['description', 'start', 'end', 'timezone', 'city', 'region',
                  'country', 'lat', 'lon', 'owner', 'external_link',
                  'functional_areas', 'estimated_attendance',
                  'planning_pad_url', 'hashtag']

    def get_functional_areas(self, event):
        """Get the active functional areas for each user."""
        items = event.categories.filter(active=True)
        serializer = FunctionalAreaSerializer(instance=items, many=True)
        return serializer.data
