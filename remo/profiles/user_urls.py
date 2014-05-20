from django.conf.urls import include, patterns, url

urlpatterns = patterns(
    'remo.profiles.views',
    url(r'^(?P<display_name>[A-Za-z0-9_]+)/$',
        'view_profile', name='profiles_view_profile'),
    url(r'^(?P<display_name>[A-Za-z0-9_]+)/edit/$',
        'edit', name='profiles_edit'),
    url(r'^(?P<display_name>[A-Za-z0-9_]+)/delete/$',
        'delete_user', name='profiles_delete'),
    url(r'^(?P<display_name>[A-Za-z0-9_]+)/r/',
        include('remo.reports.r_urls')))
