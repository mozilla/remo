from urllib import unquote

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.timezone import now

from jinja2 import escape
from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource

from remo.api import HttpCache
from remo.base.serializers import iCalSerializer
from remo.events.helpers import is_multiday
from remo.events.models import Event, EventMetric, EventMetricOutcome
from remo.reports.models import Campaign


# Legacy non-public api
class EventMetricResource(ModelResource):
    """Event Metric Resource."""

    class Meta:
        queryset = EventMetric.active_objects.all()
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        include_resource_uri = False
        include_absolute_url = False
        resource_name = 'event_metrics'
        allowed_methods = ['get']
        fields = ['name']
        filtering = {'name': ALL}


class EventMetricOutcomeResource(ModelResource):
    """Event Metric Outcome Resource."""
    metric = fields.ToOneField('remo.events.api.api_v1.EventMetricResource',
                               'metric', full=True, null=True)

    class Meta:
        queryset = EventMetricOutcome.objects.all()
        resource_name = 'event_metrics_outcome'
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        include_resource_uri = False
        include_absolute_url = False
        allowed_methods = ['get']
        fields = ['metric', 'expected_outcome', 'outcome']


class CampaignResource(ModelResource):
    """Campaign Resource."""

    class Meta:
        queryset = Campaign.active_objects.all()
        resource_name = 'campaign'
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        include_resource_uri = False
        include_absolute_url = False
        allowed_methods = ['get']
        fields = ['name']
        filtering = {'name': ALL}


class EventResource(ModelResource):
    """Event Resource."""
    local_start = fields.DateTimeField()
    local_end = fields.DateTimeField()
    owner_name = fields.CharField()
    owner_profile_url = fields.CharField()
    event_url = fields.CharField()
    multiday = fields.BooleanField()
    categories = fields.ToManyField(
        'remo.profiles.api.api_v1.FunctionalAreasResource',
        attribute='categories', full=True, null=True)
    metrics = fields.ToManyField(
        'remo.events.api.api_v1.EventMetricOutcomeResource',
        'eventmetricoutcome_set', full=True, null=True)
    swag_bug_id = fields.IntegerField(null=True)
    budget_bug_id = fields.IntegerField(null=True)
    sign_ups = fields.IntegerField()
    campaign = fields.ToOneField('remo.events.api.CampaignResource',
                                 attribute='campaign', null=True)

    class Meta:
        cache = HttpCache(control={'max_age': 1800, 's_maxage': 1800,
                                   'public': True})
        queryset = Event.objects.all()
        resource_name = 'event'
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        serializer = iCalSerializer(formats=['json', 'jsonp', 'ical'])
        allowed_methods = ['get']
        ordering = ['start', 'end']
        fields = ['name', 'start', 'end', 'timezone',
                  'venue', 'city', 'region', 'country', 'lat', 'lon',
                  'external_link', 'description', 'mozilla_event', 'owner',
                  'estimated_attendance', 'actual_attendance']
        filtering = {'name': ALL, 'city': ALL, 'region': ALL, 'country': ALL,
                     'start': ALL, 'end': ALL,
                     'categories': ALL_WITH_RELATIONS,
                     'campaign': ALL_WITH_RELATIONS}

    def dehydrate_name(self, bundle):
        """Sanitize event name."""
        return unicode(escape(bundle.obj.name))

    def dehydrate_owner_name(self, bundle):
        """Return owner fullname."""
        return bundle.obj.owner.get_full_name()

    def dehydrate_owner_profile_url(self, bundle):
        """Return owner profile url."""
        return (settings.SITE_URL +
                reverse('profiles_view_profile',
                        kwargs={'display_name':
                                bundle.obj.owner.userprofile.display_name}))

    def dehydrate_event_url(self, bundle):
        """Return event url."""
        return (settings.SITE_URL +
                reverse('events_view_event', kwargs={'slug': bundle.obj.slug}))

    def dehydrate_local_start(self, bundle):
        """Return local start datetime."""
        return bundle.obj.local_start.replace(tzinfo=None)

    def dehydrate_local_end(self, bundle):
        """Return local end datetime."""
        return bundle.obj.local_end.replace(tzinfo=None)

    def dehydrate_multiday(self, bundle):
        """Return True if event is multiday, False otherwise."""
        return is_multiday(bundle.obj.local_start, bundle.obj.local_end)

    def dehydrate_swag_bug_id(self, bundle):
        """Return the bug number for a swag request, if exists."""
        if bundle.obj.swag_bug:
            return bundle.obj.swag_bug.bug_id
        return None

    def dehydrate_budget_bug_id(self, bundle):
        """Return the bug number for a budget requests, if exists."""
        if bundle.obj.budget_bug:
            return bundle.obj.budget_bug.bug_id
        return None

    def dehydrate_sign_ups(self, bundle):
        """Return the number of the people who signed up in an event."""
        return bundle.obj.attendees.all().count()

    def apply_filters(self, request, applicable_filters):
        """Add special 'query' parameter to filter Events.

        The 'query' parameters exists in parallel with 'filter'
        parameters as defined by tastypie and EventResource schema.
        """

        base_object_list = (super(EventResource, self).
                            apply_filters(request, applicable_filters))

        query = request.GET.get('query', None)
        if query:
            query = unquote(query)
            # We need to split query to match full names
            qset = Q()
            for term in query.split():
                for key in ('owner__first_name__istartswith',
                            'owner__last_name__istartswith'):
                    qset |= Q(**{key: term})
            qset |= (Q(owner__userprofile__display_name__istartswith=query) |
                     Q(owner__userprofile__local_name__istartswith=query) |
                     Q(owner__email__istartswith=query) |
                     Q(owner__userprofile__private_email__istartswith=query) |
                     Q(country__istartswith=query) |
                     Q(region__istartswith=query) |
                     Q(city__istartswith=query) |
                     Q(name__icontains=query))

            base_object_list = base_object_list.filter(qset).distinct()

        return base_object_list

    def create_response(self, request, data, **response_kwargs):
        """Add HTTP header to specify the filename of iCal exports."""
        response = super(EventResource, self).create_response(
            request, data, **response_kwargs)

        if self.determine_format(request) == 'text/calendar':
            today = now().date()
            filename = today.strftime('ical-export-%Y-%m-%d.ics')
            response['Content-Disposition'] = 'filename="%s"' % filename

        return response
