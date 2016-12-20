from django.conf.urls import url
from django.views.generic import RedirectView

from remo.events import views as events_views

RE_PERIOD = r'period/(?P<period>\w+)/'
RE_START = r'(start/(?P<start>\d{4}\-\d{2}\-\d{2})/)?'
RE_END = r'(end/(?P<end>\d{4}\-\d{2}\-\d{2})/)?'
RE_SEARCH = r'(search/(?P<search>.+?)/)?'

urlpatterns = [
    url(r'^new/$', events_views.edit_event, name='events_new_event'),
    url(r'^new$', RedirectView.as_view(url='new/', permanent=True)),
    url(r'^$', events_views.list_events, name='events_list_events'),
    url(r'^' + RE_PERIOD + RE_START + RE_END + RE_SEARCH + 'ical/$',
        events_views.multiple_event_ical, name='multiple_event_ical'),
    # This url is intentionally left without a $
    url(r'^', events_views.redirect_list_events, name='events_list_profiles_redirect'),
]
