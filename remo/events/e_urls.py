from django.conf.urls import url

from remo.events import views as events_views

urlpatterns = [
    url(r'^(?P<slug>[a-z0-9-]+)/$', events_views.view_event, name='events_view_event'),
    url(r'^(?P<slug>[a-z0-9-]+)/edit/$', events_views.edit_event, name='events_edit_event'),
    url(r'^(?P<slug>[a-z0-9-]+)/clone/$', events_views.edit_event, {'clone': True},
        name='events_clone_event'),
    url(r'^(?P<slug>[a-z0-9-]+)/delete/$', events_views.delete_event, name='events_delete_event'),
    url(r'^(?P<slug>[a-z0-9-]+)/delete/comment/(?P<pk>\d+)/$',
        events_views.delete_event_comment, name='events_delete_event_comment'),
    url(r'^(?P<slug>[a-z0-9-]+)/subscribe/$', events_views.manage_subscription,
        {'subscribe': True}, name='events_subscribe_to_event'),
    url(r'^(?P<slug>[a-z0-9-]+)/unsubscribe/$', events_views.manage_subscription,
        {'subscribe': False}, name='events_unsubscribe_from_event'),
    url(r'^(?P<slug>[a-z0-9-]+)/ical/$', events_views.export_single_event_to_ical,
        name='events_icalendar_event'),
    url(r'^(?P<slug>[a-z0-9-]+)/emailattendees/$', events_views.email_attendees,
        name='email_attendees'),
]
