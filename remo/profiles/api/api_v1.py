from datetime import timedelta
from urllib import unquote

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import QueryDict
from django.utils.timezone import now

from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource

from remo.api import HttpCache
from remo.base.serializers import CSVSerializer
from remo.profiles.helpers import get_avatar_url
from remo.profiles.models import UserProfile, FunctionalArea
from remo.reports.models import NGReport
from remo.reports.utils import get_last_report


class FunctionalAreasResource(ModelResource):
    """Functional Areas Resource."""

    class Meta:
        queryset = FunctionalArea.active_objects.all()
        resource_name = 'functionalareas'
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        include_resource_uri = False
        include_absolute_url = False
        allowed_methods = ['get']
        fields = ['name']
        filtering = {'name': ALL}


class ProfileResource(ModelResource):
    """Profile Resource."""
    profile_url = fields.CharField()
    avatar_url = fields.CharField()
    is_mentor = fields.BooleanField()
    is_council = fields.BooleanField()
    functional_areas = fields.ToManyField(FunctionalAreasResource,
                                          attribute='functional_areas',
                                          full=True, null=True)
    mentor = fields.ToOneField('remo.profiles.api.api_v1.RepResource',
                               attribute='mentor')
    last_report_date = fields.DateField()

    class Meta:
        queryset = UserProfile.objects.filter(registration_complete=True)
        resource_name = 'profile'
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        include_resource_uri = False
        include_absolute_url = False
        allowed_methods = ['get']
        fields = ['city', 'region', 'country', 'display_name', 'local_name',
                  'lon', 'lat', 'mozillians_profile_url', 'twitter_account',
                  'facebook_url', 'diaspora_url', 'personal_blog_feed',
                  'irc_name']
        ordering = ['country']
        filtering = {'display_name': ALL,
                     'local_name': ALL,
                     'irc_name': ALL,
                     'country': ALL,
                     'region': ALL,
                     'city': ALL,
                     'functional_areas': ALL_WITH_RELATIONS}

    def dehydrate(self, bundle):
        """Prepare bundle.data for CSV export."""
        if bundle.request.method == 'GET':
            req = bundle.request.GET
            if req.get('format') == 'csv':
                bundle.data.pop('functional_areas', None)
                bundle.data.pop('personal_blog_feed', None)
                bundle.data.pop('profile_url', None)
        return bundle

    def dehydrate_profile_url(self, bundle):
        """Calculate and return full url to Rep profile."""
        return (settings.SITE_URL + reverse('profiles_view_profile',
                                            kwargs={'display_name':
                                                    bundle.obj.display_name}))

    def dehydrate_avatar_url(self, bundle):
        """Calculate and return full avatar of Rep."""
        return get_avatar_url(bundle.obj.user, -1)

    def dehydrate_is_mentor(self, bundle):
        """Calculate and return if user is mentor."""
        return bundle.obj.user.groups.filter(name='Mentor').count() == 1

    def dehydrate_is_council(self, bundle):
        """Calculate and return if user is counselor."""
        return bundle.obj.user.groups.filter(name='Council').count() == 1

    def dehydrate_last_report_date(self, bundle):
        start_period = now().date() - timedelta(weeks=4)
        end_period = now().date() + timedelta(weeks=4)
        reports = bundle.obj.user.ng_reports.filter(
            report_date__range=(start_period, end_period))
        try:
            return reports.latest('report_date').report_date
        except NGReport.DoesNotExist:
            report = get_last_report(bundle.obj.user)
            if report:
                return report.report_date
            return None


class RepResource(ModelResource):
    """Rep Resource."""
    fullname = fields.CharField(attribute='get_full_name')
    profile = fields.ToOneField(ProfileResource, attribute='userprofile',
                                full=True, null=True)

    class Meta:
        cache = HttpCache(control={'max_age': 3600, 'public': True,
                                   's-maxage': 3600})
        queryset = User.objects.filter(userprofile__registration_complete=True,
                                       groups__name='Rep')
        resource_name = 'rep'
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        serializer = CSVSerializer(formats=['json', 'jsonp', 'csv'])
        allowed_methods = ['get']
        fields = ['first_name', 'last_name']
        ordering = ['profile', 'first_name', 'last_name']
        filtering = {'first_name': ALL,
                     'last_name': ALL,
                     'profile': ALL_WITH_RELATIONS}

    def apply_filters(self, request, applicable_filters):
        """Add special 'query' parameter to filter Reps.

        When 'query' parameter is present, Rep list is filtered by last
        name, first name, display name and local name with a case
        insensitive matching method.

        The 'query' parameters exists in parallel with 'filter'
        parameters as defined by tastypie and RepResource schema.
        """

        base_object_list = (super(RepResource, self).
                            apply_filters(request, applicable_filters))

        query = request.GET.get('query', None)
        if query:
            query = unquote(query)
            # We need to split query to match full names
            qset = Q()
            for term in query.split():
                for key in ('first_name__istartswith',
                            'last_name__istartswith'):
                    qset |= Q(**{key: term})
            qset |= (Q(userprofile__display_name__istartswith=query) |
                     Q(userprofile__local_name__istartswith=query) |
                     Q(userprofile__irc_name__istartswith=query) |
                     Q(email__istartswith=query) |
                     Q(userprofile__private_email__istartswith=query) |
                     Q(userprofile__country__istartswith=query) |
                     Q(userprofile__region__istartswith=query) |
                     Q(userprofile__city__istartswith=query) |
                     Q(userprofile__functional_areas__name__istartswith=query))

            base_object_list = base_object_list.filter(qset).distinct()

        group = request.GET.get('group', None)
        if group:
            if group == 'mentor':
                base_object_list = (base_object_list.
                                    filter(groups__name='Mentor'))
            elif group == 'council':
                base_object_list = (base_object_list.
                                    filter(groups__name='Council'))
            elif group == 'rep':
                base_object_list = (base_object_list.
                                    filter(groups__name='Rep'))

        return base_object_list

    def dehydrate(self, bundle):
        """Prepare bundle.data for CSV export."""
        if bundle.request.method == 'GET':
            req = bundle.request.GET
            if req.get('format') == 'csv':
                bundle.data.pop('fullname', None)
                bundle.data.pop('resource_uri', None)
        return bundle

    def apply_sorting(self, obj_list, options=None):
        """Add support for multiple order_by parameters."""
        if ',' in options.get('order_by', ''):
            order_by_values = []
            for param in options['order_by'].split(','):
                q = QueryDict('order_by=%s' % param)
                obj_list = super(RepResource, self).apply_sorting(obj_list, q)
                order_by_values.append(obj_list.query.order_by[0])

            return obj_list.order_by(*order_by_values)

        return super(RepResource, self).apply_sorting(obj_list, options)

    def create_response(self, request, data, **response_kwargs):
        """Add HTTP header to specify the filename of CSV exports."""
        response = super(RepResource, self).create_response(
            request, data, **response_kwargs)

        if self.determine_format(request) == 'text/csv':
            today = now().date()
            filename = today.strftime('reps-export-%Y-%m-%d.csv')
            response['Content-Disposition'] = 'filename="%s"' % filename

        return response
