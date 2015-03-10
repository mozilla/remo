from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

from remo.events.api.serializers import (EventDetailedSerializer,
                                         EventSerializer)
from remo.events.models import Event


class EventsViewSet(ReadOnlyModelViewSet):
    """Return a list of events."""
    serializer_class = EventSerializer
    model = Event
    queryset = Event.objects.all()

    def retrieve(self, request, pk):
        event = get_object_or_404(self.queryset, pk=pk)
        serializer = EventDetailedSerializer(event,
                                             context={'request': request})
        return Response(serializer.data)
