from rest_framework import serializers

from remo.base.templatetags.helpers import absolutify
from remo.events.api.serializers import EventSerializer
from remo.profiles.api.serializers import (FunctionalAreaSerializer,
                                           UserSerializer)
from remo.reports.models import NGReport


class ActivitiesSerializer(serializers.ModelSerializer):
    """Serializer for the NGReport model."""
    activity = serializers.ReadOnlyField(source='activity.name')

    class Meta:
        model = NGReport
        fields = ['activity', '_url']


class ActivitiesDetailedSerializer(serializers.HyperlinkedModelSerializer):
    """Detailed serializer for the NGReport model."""

    user = UserSerializer()
    activity = serializers.ReadOnlyField(source='activity.name')
    initiative = serializers.ReadOnlyField(source='campaign.name')
    mentor = UserSerializer()
    passive_report = serializers.ReadOnlyField(source='is_passive')
    event = EventSerializer()
    functional_areas = FunctionalAreaSerializer(many=True)
    remo_url = serializers.SerializerMethodField()
    report_date = serializers.DateTimeField(format='%Y-%m-%d')

    class Meta:
        model = NGReport
        fields = ['user', 'activity', 'initiative', 'functional_areas',
                  'activity_description', 'report_date', 'mentor', 'location',
                  'longitude', 'latitude', 'link', 'link_description',
                  'passive_report', 'event', 'remo_url']

    def get_remo_url(self, obj):
        """
        Default method for fetching the activity url in ReMo portal.
        """
        return absolutify(obj.get_absolute_url())
