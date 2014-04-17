from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    '',
    url(r'^$', 'remo.base.views.edit_settings', name='edit_settings'),
    url(r'^availability/(?P<display_name>[A-Za-z0-9_]+)/$',
        'remo.base.views.edit_availability', name='edit_availability'),
)
