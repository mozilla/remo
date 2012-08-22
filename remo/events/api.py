from urllib import unquote

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q

from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.constants import ALL
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer

from remo.api import ClientCachedResource

from helpers import is_multiday
from models import Event


class EventResource(ClientCachedResource, ModelResource):
    """Event Resource."""
    local_start = fields.DateTimeField()
    local_end = fields.DateTimeField()
    owner_name = fields.CharField()
    owner_profile_url = fields.CharField()
    event_url = fields.CharField()
    multiday = fields.BooleanField()

    class Meta:
        cache_control = {"max_age": 1800, "s_maxage": 1800}
        queryset = Event.objects.all()
        resource_name = 'event'
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        serializer = Serializer(formats=['json', 'jsonp'])
        allowed_methods = ['get']
        fields = ['name', 'start', 'end', 'timezone',
                  'venue', 'city', 'region', 'country', 'lat', 'lon',
                  'external_link', 'description', 'mozilla_event', 'owner',
                  'estimated_attendance']
        filtering = {'name': ALL, 'city': ALL, 'region': ALL, 'country': ALL,
                     'start': ALL, 'end': ALL}

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
        return bundle.obj.local_start

    def dehydrate_local_end(self, bundle):
        """Return local end datetime."""
        return bundle.obj.local_end

    def dehydrate_multiday(self, bundle):
        """Return True if event is multiday, False otherwise."""
        return is_multiday(bundle.obj)

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
            qset |= (Q(owner__userprofile__display_name__istartswith=query)|
                     Q(owner__userprofile__local_name__istartswith=query)|
                     Q(owner__email__istartswith=query)|
                     Q(owner__userprofile__private_email__istartswith=query)|
                     Q(country__istartswith=query)|
                     Q(region__istartswith=query)|
                     Q(city__istartswith=query)|
                     Q(name__icontains=query))

            base_object_list = base_object_list.filter(qset).distinct()

        return base_object_list
