from django.conf.urls import include, url

from rest_framework import routers
from tastypie.api import Api

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
    """Project specific base DRF router."""
    def get_api_root_view(self):
        api_root_view = super(RemoRouter, self).get_api_root_view()
        APIRootClass = api_root_view.cls

        class RemoAPIRoot(APIRootClass):
            """Amends APIRoot repsonse to add CORS headers."""
            def dispatch(self, *args, **kwargs):
                response = super(RemoAPIRoot, self).dispatch(*args, **kwargs)
                response['Access-Control-Allow-Origin'] = '*'
                return response

        return RemoAPIRoot.as_view()


router = RemoRouter()
router.register(r'users', UserProfileViewSet)
router.register(r'events', EventsViewSet)
router.register(r'activities', ActivitiesViewSet)

urlpatterns = [
    url(r'', include(v1_api.urls)),
    url(r'^remo/v1/', include(router.urls), name='v1root'),
    url(r'^kpi/events/', EventsKPIView.as_view(), name='kpi-events'),
    url(r'^kpi/activities/', ActivitiesKPIView.as_view(), name='kpi-activities'),
    url(r'^kpi/people/', PeopleKPIView.as_view(), name='kpi-people')
]
