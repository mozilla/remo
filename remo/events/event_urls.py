from django.conf.urls.defaults import patterns, url


RE_PERIOD = r'period/(?P<period>\w+)/'
RE_START = r'(start/(?P<start>\d{4}\-\d{2}\-\d{2})/)?'
RE_END = r'(end/(?P<end>\d{4}\-\d{2}\-\d{2})/)?'
RE_SEARCH = r'(search/(?P<search>[\w,\s]+)/)?'

urlpatterns = patterns(
    '',
    url(r'^new/$', 'remo.events.views.edit_event', name='events_new_event'),
    url(r'^new$', 'django.views.generic.simple.redirect_to',
        {'url': 'new/', 'permanent': True}),
    url(r'^$', 'remo.events.views.list_events', name='events_list_events'),
    url(r'^' + RE_PERIOD + RE_START + RE_END + RE_SEARCH + 'ical/$',
        'remo.events.views.multiple_event_ical', name='multiple_event_ical'),
    # This url is intentionally left without a $
    url(r'^', 'remo.events.views.redirect_list_events',
        name='events_list_profiles_redirect'),
)
