from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q

from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer

from remo.profiles.helpers import get_avatar_url
from remo.profiles.models import UserProfile


class ProfileResource(ModelResource):
    """Profile Resource."""
    profile_url = fields.CharField()
    avatar_url = fields.CharField()

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
                  'facebook_url', 'diaspora_url', 'personal_blog_feed']
        filtering = {'display_name': ALL,
                     'local_name': ALL}

    def dehydrate_profile_url(self, bundle):
        """Calculate and return full url to Rep profile."""
        return (settings.SITE_URL + reverse('profiles_view_profile',
                                            kwargs={'display_name':
                                                    bundle.obj.display_name}))

    def dehydrate_avatar_url(self, bundle):
        """Calculate and return full avatar of Rep."""
        return get_avatar_url(bundle.obj.user, -1)


class RepResource(ModelResource):
    """Rep Resource."""
    fullname = fields.CharField(attribute='get_full_name')
    profile = fields.ToOneField(ProfileResource, attribute='userprofile',
                                full=True, null=True)

    class Meta:
        queryset = User.objects.filter(userprofile__registration_complete=True)
        resource_name = 'rep'
        authentication = Authentication()
        authorization = ReadOnlyAuthorization()
        serializer = Serializer(formats=['json', 'jsonp'])
        allowed_methods = ['get']
        fields = ['email', 'first_name', 'last_name']
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
            qset = (Q(first_name__icontains=query)|
                    Q(last_name__icontains=query)|
                    Q(userprofile__display_name__icontains=query)|
                    Q(userprofile__local_name__icontains=query))
            base_object_list = base_object_list.filter(qset).distinct()

        return base_object_list
