from django.shortcuts import get_object_or_404

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

from remo.reports.api.serializers import (ActivitiesDetailedSerializer,
                                          ActivitiesSerializer)
from remo.reports.models import NGReport


class ActivitiesViewSet(ReadOnlyModelViewSet):
    """Return a list of activities."""
    serializer_class = ActivitiesSerializer
    model = NGReport
    queryset = NGReport.objects.all()

    def retrieve(self, request, pk):
        report = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = ActivitiesDetailedSerializer(report,
                                                  context={'request': request})
        return Response(serializer.data)
