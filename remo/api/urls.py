from django.conf.urls.defaults import *
from tastypie.api import Api

from remo.events.api import EventResource
from remo.profiles.api import RepResource

v1_api = Api(api_name='v1')
v1_api.register(RepResource())
v1_api.register(EventResource())

urlpatterns = patterns('', url(r'', include(v1_api.urls)))
