from collections import namedtuple
from datetime import datetime, timedelta

from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

import django_filters
from rest_framework.views import APIView
from rest_framework.response import Response

from remo.profiles.api.serializers import (PeopleKPISerializer,
                                           UserProfileDetailedSerializer,
                                           UserSerializer)
from remo.api.views import BaseReadOnlyModelViewset
from remo.base.utils import get_quarter
from remo.profiles.models import UserProfile


KPI_WEEKS = 12
# Number of activities
CORE = 4
ACTIVE = 1
CASUAL = 1
INACTIVE = 0
# Activities Thresholds:
# The max period in which we are looking to find reports for a user
# both in past and future, measured in weeks
CASUAL_INACTIVE = 4
ACTIVE_CORE = 2


class UserProfileFilter(django_filters.FilterSet):
    groups = django_filters.CharFilter(name='groups__name')
    functional_areas = django_filters.CharFilter(
        name='userprofile__functional_areas__name')
    mentor = django_filters.CharFilter(name='userprofile__mentor')
    city = django_filters.CharFilter(name='userprofile__city')
    region = django_filters.CharFilter(name='userprofile__region')
    country = django_filters.CharFilter(name='userprofile__country')
    twitter = django_filters.CharFilter(name='userprofile__twitter_account')
    jabber = django_filters.CharFilter(name='userprofile__jabber_id')
    irc_name = django_filters.CharFilter(name='userprofile__irc_name')
    wiki_profile = django_filters.CharFilter(
        name='userprofile__wiki_profile_url')
    irc_channels = django_filters.CharFilter(name='userprofile__irc_channels')
    linkedin = django_filters.CharFilter(name='userprofile__linkedin_url')
    facebook = django_filters.CharFilter(name='userprofile__facebook_url')
    diaspora = django_filters.CharFilter(name='userprofile__diaspora_url')

    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class UserProfileViewSet(BaseReadOnlyModelViewset):
    """Returns a list of Reps profiles."""
    serializer_class = UserSerializer
    model = User
    queryset = User.objects.all()
    filter_class = UserProfileFilter

    def get_queryset(self):
        queryset = self.queryset.filter(
            groups__name='Rep', userprofile__registration_complete=True)
        return queryset

    def retrieve(self, request, pk):
        user = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = UserProfileDetailedSerializer(
            user.userprofile, context={'request': request})
        return Response(serializer.data)


class PeopleKPIFilter(django_filters.FilterSet):
    """Filter for People KPI end-point."""
    category = django_filters.CharFilter(
        name='userprofile__functional_areas__name')
    initiative = django_filters.CharFilter(
        name='ng_reports__campaign__name')
    country = django_filters.CharFilter(name='userprofile__country')

    class Meta:
        model = UserProfile
        fields = ['country', 'category', 'initiative']


class PeopleKPIView(APIView):

    def get(self, request):
        """Returns serialized data for People KPI."""

        queryset = User.objects.filter(groups__name='Rep',
                                       userprofile__registration_complete=True)
        people = PeopleKPIFilter(request.query_params, queryset=queryset)
        weeks = int(request.query_params.get('weeks', KPI_WEEKS))

        # Total number of Reps
        total = people.count()

        # Total Reps added in the last quarter
        joined_date = get_quarter()[1]
        quarter_total = people.qs.filter(
            userprofile__date_joined_program__gte=joined_date).count()

        # Current quarter start
        current_quarter_start = get_quarter()[1]

        # Total Reps joined the previous quarter
        previous_quarter_end = current_quarter_start - timedelta(days=1)
        previous_quarter_start = get_quarter(previous_quarter_end)[1]
        total_reps_range = [previous_quarter_start, previous_quarter_end]
        previous_quarter_total = people.qs.filter(
            userprofile__date_joined_program__range=total_reps_range).count()

        diff = quarter_total - previous_quarter_total
        try:
            # Percentage change of events compared with previous week
            quarter_ratio = diff / float(previous_quarter_total) * 100
        except ZeroDivisionError:
            if diff > 0:
                quarter_ratio = 100
            else:
                quarter_ratio = 0

        # Total Reps added this week
        today = datetime.combine(now().date(), datetime.min.time())
        current_week_start = today - timedelta(days=now().weekday())
        prev_week_start = current_week_start - timedelta(weeks=1)

        week_total = people.qs.filter(
            userprofile__date_joined_program__gte=current_week_start).count()

        # Total Reps added the previous week
        query_range = [prev_week_start, current_week_start]
        prev_week_total = people.qs.filter(
            userprofile__date_joined_program__range=query_range).count()

        diff = week_total - prev_week_total
        try:
            # Percentage change of events compared with previous week
            week_ratio = diff / float(prev_week_total) * 100
        except ZeroDivisionError:
            if diff > 0:
                week_ratio = 100
            else:
                week_ratio = 0

        weekly_count = []
        for i in range(weeks):
            start = current_week_start - timedelta(weeks=i)
            end = start + timedelta(weeks=1)

            # Total number of reps (per week) for the past 6 weeks
            count = people.qs.filter(
                userprofile__date_joined_program__range=[start, end]).count()
            weekly_count.append({'week': weeks - i, 'people': count})

        # Get the number of reports for each user.

        # Activity metrics:
        # Inactive: No activity within 8 weeks (4 past, 4 future)
        # Casual: 1 activity within 8 weeks (4 past, 4 future)
        # Active: 1 activity within 4 weeks (2 past, 2 future)
        # Core: 4 activities within 4 weeks (2 past, 2 future)
        def get_activity_query(query, start_date=None, offset=0, invert=False):
            if not start_date:
                start_date = today
            date_range = [start_date - timedelta(weeks=offset),
                          start_date + timedelta(weeks=offset)]
            q_args = Q(ng_reports__report_date__range=date_range)
            if invert:
                q_args = ~q_args
            return (query.filter(q_args).distinct()
                    .annotate(num_reports=Count('ng_reports')))

        core_active_query = get_activity_query(people.qs, offset=ACTIVE_CORE)
        # Active contributors - 8 weeks
        active_contributors = core_active_query.filter(num_reports__gte=ACTIVE,
                                                       num_reports__lt=CORE)
        num_active = active_contributors.count()
        # Core contributors - 8 weeks
        num_core = core_active_query.filter(num_reports__gte=CORE).count()

        # Inactive contributors - 16 weeks
        num_inactive = get_activity_query(people.qs,
                                          offset=CASUAL_INACTIVE,
                                          invert=True).count()
        # Casual contributors
        active_ids = core_active_query.values_list('id', flat=True)
        num_casual = (get_activity_query(people.qs,
                                         offset=CASUAL_INACTIVE)
                      .exclude(id__in=active_ids).count())

        weekly_contribution = []
        for i in range(weeks):
            start = current_week_start - timedelta(weeks=i)

            # Conversion points per week
            core_active_query = get_activity_query(people.qs,
                                                   start_date=start,
                                                   offset=ACTIVE_CORE)
            # Active contributors
            active_contributors = core_active_query.filter(
                num_reports__gte=ACTIVE, num_reports__lt=CORE)
            active_weekly = active_contributors.count()
            # Core contributors
            core_weekly = core_active_query.filter(
                num_reports__gte=CORE).count()

            # Inactive contributors
            inactive_weekly = get_activity_query(people.qs,
                                                 start_date=start,
                                                 offset=CASUAL_INACTIVE,
                                                 invert=True).count()
            # Casual contributors
            active_ids = core_active_query.values_list('id', flat=True)
            casual_weekly = (get_activity_query(people.qs,
                                                start_date=start,
                                                offset=CASUAL_INACTIVE)
                             .exclude(id__in=active_ids).count())

            weekly_contribution.append({'week': weeks - i,
                                        'core': core_weekly,
                                        'active': active_weekly,
                                        'casual': casual_weekly,
                                        'inactive': inactive_weekly
                                        })

        kwargs = {
            'total': total,
            'quarter_total': quarter_total,
            'quarter_growth_percentage': quarter_ratio,
            'week_total': week_total,
            'week_growth_percentage': week_ratio,
            'total_per_week': weekly_contribution,
            'inactive_week': num_inactive,
            'casual_week': num_casual,
            'active_week': num_active,
            'core_week': num_core
        }

        kpi = namedtuple('PeopleKPI', kwargs.keys())(*kwargs.values())
        serializer = PeopleKPISerializer(kpi)

        return Response(serializer.data)
