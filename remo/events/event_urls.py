from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^new/$', 'remo.events.views.edit_event', name='events_new_event'),
    url(r'^new$', 'django.views.generic.simple.redirect_to',
        {'url': 'new/', 'permanent': True}),
    url(r'^$', 'remo.events.views.list_events', name='events_list_events'),
    # This url is intentionally left without a $
    url(r'^', 'remo.events.views.redirect_list_events',
        name='events_list_profiles_redirect'),
)
