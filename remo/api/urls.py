from django.conf.urls import include, patterns, url

from rest_framework import routers
from tastypie.api import Api

from remo.events.api.api_v1 import EventResource
from remo.events.api.views import EventsViewSet
from remo.profiles.api.api_v1 import RepResource
from remo.profiles.api.views import UserProfileViewSet
from remo.reports.api.views import ActivitiesViewSet


# Legacy non-public API
v1_api = Api(api_name='v1')
v1_api.register(RepResource())
v1_api.register(EventResource())

# ReMo public API
router = routers.DefaultRouter()
router.register(r'users', UserProfileViewSet)
router.register(r'events', EventsViewSet)
router.register(r'activities', ActivitiesViewSet)

urlpatterns = patterns(
    '',
    url(r'', include(v1_api.urls)),
    url(r'^beta/', include(router.urls), name='v1root'),
)
