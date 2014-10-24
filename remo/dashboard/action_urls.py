from django.conf.urls import patterns, url


# Action items urls
urlpatterns = patterns(
    'remo.dashboard.views',
    url(r'^$', 'list_action_items', name='list_action_items'),
)
