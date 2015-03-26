import math
from collections import namedtuple
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.utils.timezone import now

import django_filters
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

from remo.events.api.serializers import (EventDetailedSerializer,
                                         EventSerializer, EventsKPISerializer)
from remo.events.models import Event


KPI_WEEKS = 6


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


class EventsKPIFilter(django_filters.FilterSet):
    class Meta:
        model = Event
        fields = ['categories__name', 'campaign__name', 'country']


class EventsKPIView(APIView):

    def get(self, request):
        """Returns serialized data for Events KPI"""

        queryset = Event.objects.filter(start__lte=now())
        events = EventsKPIFilter(request.GET, queryset=queryset)
        weeks = int(request.QUERY_PARAMS.get('weeks', KPI_WEEKS))

        # Total calculations
        total = events.qs.count()

        # Quarter calculations
        current_quarter = int(math.ceil(now().month/3.0))
        current_quarter_start = datetime(now().year, current_quarter, 1)
        quarter_total = events.qs.filter(
            start__gte=current_quarter_start).count()

        # Total events until start of quarter
        quarter_s_total = events.qs.filter(
            start__lte=current_quarter_start).count()

        try:
            percent_quarter = (total-quarter_s_total)/float(quarter_s_total)
        except ZeroDivisionError:
            percent_quarter = 0

        # Week calculations
        current_week_start = now() - timedelta(days=now().weekday())
        prev_week_start = current_week_start - timedelta(weeks=1)
        week_total = events.qs.filter(start__gte=current_week_start).count()
        query_range = [prev_week_start, current_week_start]
        prev_week_total = events.qs.filter(start__range=query_range).count()

        try:
            percent_week = (week_total-prev_week_total)/float(prev_week_total)
        except ZeroDivisionError:
            percent_week = 0

        weekly_count = []

        for i in range(weeks):
            start = current_week_start - timedelta(weeks=i)
            end = start + timedelta(weeks=1)
            count = events.qs.filter(start__range=[start, end]).count()
            weekly_count.append({'week': weeks-i, 'events': count})

        kwargs = {
            'total': total,
            'total_quarter': quarter_total,
            'percentage_quarter': percent_quarter*100,
            'total_week': week_total,
            'percentage_week': percent_week*100,
            'total_per_week': weekly_count
        }

        kpi = namedtuple('EventsKPI', kwargs.keys())(*kwargs.values())
        serializer = EventsKPISerializer(kpi)

        return Response(serializer.data)
