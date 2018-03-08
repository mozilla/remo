from collections import namedtuple
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.utils.timezone import now

import django_filters
from rest_framework.views import APIView
from rest_framework.response import Response

from remo.api.serializers import BaseKPISerializer
from remo.api.views import BaseReadOnlyModelViewset
from remo.base.utils import get_quarter
from remo.events.api.serializers import (EventDetailedSerializer,
                                         EventSerializer)
from remo.events.models import Event


KPI_WEEKS = 12


class EventsFilter(django_filters.FilterSet):
    owner = django_filters.CharFilter(name='owner__userprofile')
    categories = django_filters.CharFilter(name='categories__name')
    initiative = django_filters.CharFilter(name='campaign__name')

    class Meta:
        model = Event
        fields = ('name', 'description', 'start', 'end', 'city', 'region',
                  'country', 'lat', 'lon')


class EventsViewSet(BaseReadOnlyModelViewset):
    """Return a list of events."""
    serializer_class = EventSerializer
    model = Event
    queryset = Event.objects.all()
    filter_class = EventsFilter

    def retrieve(self, request, pk):
        event = get_object_or_404(self.queryset, pk=pk)
        serializer = EventDetailedSerializer(event,
                                             context={'request': request})
        return Response(serializer.data)

    def get_queryset(self):
        orderby = self.request.query_params.get('orderby', 'DESC')

        if orderby == 'DESC':
            self.queryset = self.queryset.order_by('-start')
        return self.queryset


class EventsKPIFilter(django_filters.FilterSet):
    """Filter for events KPI endpoint."""
    category = django_filters.CharFilter(name='categories__name')
    initiative = django_filters.CharFilter(name='campaign__name')

    class Meta:
        model = Event
        fields = ['country', 'category', 'initiative']


class EventsKPIView(APIView):

    def get(self, request):
        """Returns serialized data for Events KPI"""

        qs = Event.objects.filter(start__lte=now())
        events = EventsKPIFilter(request.query_params, queryset=qs)
        weeks = int(request.query_params.get('weeks', KPI_WEEKS))

        # Total number of events to day
        total = events.qs.count()

        # Quarter calculations
        current_quarter_start = get_quarter()[1]

        # Total number of events for current quarter
        quarter_total = events.qs.filter(
            start__gte=current_quarter_start).count()

        # Total number of events for the previous quarter
        previous_quarter_end = current_quarter_start - timedelta(days=1)
        previous_quarter_start = get_quarter(previous_quarter_end)[1]
        previous_quarter_total = events.qs.filter(
            start__range=[previous_quarter_start,
                          previous_quarter_end]).count()

        diff = quarter_total - previous_quarter_total
        try:
            # Percentage change of events since start of quarter
            percent_quarter = diff / float(previous_quarter_total)
        except ZeroDivisionError:
            if diff > 0:
                percent_quarter = 100
            else:
                percent_quarter = 0

        # Week calculations
        today = datetime.combine(now().date(), datetime.min.time())
        current_week_start = today - timedelta(days=now().weekday())
        prev_week_start = current_week_start - timedelta(weeks=1)

        # Total number of events this week
        week_total = events.qs.filter(start__gte=current_week_start).count()
        query_range = [prev_week_start, current_week_start]

        # Total number of events for previous week
        prev_week_total = events.qs.filter(start__range=query_range).count()

        diff = week_total - prev_week_total
        try:
            # Percentage change of events compared with previous week
            percent_week = diff / float(prev_week_total)
        except ZeroDivisionError:
            if diff > 0:
                percent_week = 100
            else:
                percent_week = 0

        weekly_count = []

        for i in range(weeks):
            start = current_week_start - timedelta(weeks=i)
            end = start + timedelta(weeks=1)

            # Total number of events (per week) for previous weeks
            count = events.qs.filter(start__range=[start, end]).count()
            weekly_count.append({'week': weeks - i, 'events': count})

        kwargs = {
            'total': total,
            'quarter_total': quarter_total,
            'quarter_growth_percentage': percent_quarter * 100,
            'week_total': week_total,
            'week_growth_percentage': percent_week * 100,
            'total_per_week': weekly_count
        }

        kpi = namedtuple('EventsKPI', kwargs.keys())(*kwargs.values())
        serializer = BaseKPISerializer(kpi)

        return Response(serializer.data)
