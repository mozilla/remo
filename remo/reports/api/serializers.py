from rest_framework import serializers

from remo.base.helpers import absolutify
from remo.events.api.serializers import EventSerializer
from remo.profiles.api.serializers import (FunctionalAreaSerializer,
                                           UserSerializer)
from remo.reports.models import NGReport


class ActivitiesSerializer(serializers.ModelSerializer):
    """Serializer for the NGReport model."""

    activity_name = serializers.ReadOnlyField(source='activity.name')
    report_url = serializers.SerializerMethodField()

    class Meta:
        model = NGReport
        fields = ['activity_name', 'report_url', '_url']

    def get_report_url(self, obj):
        """
        Default method for fetching the activity url in ReMo portal.
        """
        return absolutify(obj.get_absolute_url())


class ActivitiesDetailedSerializer(serializers.HyperlinkedModelSerializer):
    """Detailed serializer for the NGReport model."""

    user = UserSerializer()
    initiative = serializers.ReadOnlyField(source='campaign.name')
    mentor = UserSerializer()
    passive_report = serializers.ReadOnlyField(source='is_passive')
    event = EventSerializer()
    functional_areas = serializers.SerializerMethodField()

    class Meta:
        model = NGReport
        fields = ['user', 'initiative', 'functional_areas',
                  'activity_description', 'report_date', 'mentor', 'location',
                  'longitude', 'latitude', 'link', 'link_description',
                  'passive_report', 'event']

    def get_functional_areas(self, report):
        """Get the active functional areas for each report."""
        items = report.functional_areas.filter(active=True)
        serializer = FunctionalAreaSerializer(instance=items, many=True)
        return serializer.data
