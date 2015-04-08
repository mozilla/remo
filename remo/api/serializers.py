from rest_framework import serializers


class BaseKPISerializer(serializers.Serializer):
    """Serializer for the KPI data."""
    total = serializers.IntegerField()
    quarter_total = serializers.IntegerField()
    quarter_growth_percentage = serializers.FloatField()
    week_total = serializers.IntegerField()
    week_growth_percentage = serializers.FloatField()
    total_per_week = serializers.ListField()
