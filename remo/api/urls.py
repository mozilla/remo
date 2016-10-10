from django.conf.urls import include, patterns, url
from django.core.urlresolvers import NoReverseMatch

from rest_framework import routers
from rest_framework.compat import get_resolver_match, OrderedDict
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from tastypie.api import Api

from remo.api.views import BaseAPIRoot
from remo.events.api.api_v1 import EventResource
from remo.events.api.views import EventsKPIView, EventsViewSet
from remo.profiles.api.api_v1 import RepResource
from remo.reports.api.views import ActivitiesKPIView, ActivitiesViewSet
from remo.profiles.api.views import PeopleKPIView, UserProfileViewSet


# Legacy non-public API
v1_api = Api(api_name='v1')
v1_api.register(RepResource())
v1_api.register(EventResource())

# ReMo public API
class RemoRouter(routers.DefaultRouter):

    def get_api_root_view(self):
        """
        Return a view to use as the API root.
        """
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        class APIRoot(APIView):
            _ignore_model_permissions = True

            def get(self, request, *args, **kwargs):
                ret = OrderedDict()
                namespace = get_resolver_match(request).namespace
                for key, url_name in api_root_dict.items():
                    if namespace:
                        url_name = namespace + ':' + url_name
                    try:
                        ret[key] = reverse(
                            url_name,
                            request=request,
                            format=kwargs.get('format', None)
                        )
                    except NoReverseMatch:
                        # Don't bail out if eg. no list routes exist, only detail routes.
                        continue
                # Add CORS
                self.headers['Access-Control-Allow-Origin'] = '*'

                return Response(ret)

        return APIRoot.as_view()


router = RemoRouter()
router.register(r'users', UserProfileViewSet)
router.register(r'events', EventsViewSet)
router.register(r'activities', ActivitiesViewSet)

urlpatterns = patterns(
    '',
    url(r'', include(v1_api.urls)),
    url(r'^remo/v1/', include(router.urls), name='v1root'),
    url(r'^kpi/events/', EventsKPIView.as_view(), name='kpi-events'),
    url(r'^kpi/activities/', ActivitiesKPIView.as_view(),
        name='kpi-activities'),
    url(r'^kpi/people/', PeopleKPIView.as_view(), name='kpi-people')
)
