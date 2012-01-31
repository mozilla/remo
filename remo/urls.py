from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns(
    '',

    # landing page
    url(r'^$', 'remo.profiles.views.main', name='main'),

    # profiles
    url(r'^/u/(?P<display_name>[A-Za-z0-9_])/$',
        'remo.profiles.views.view_profile', name='profiles_view_profile'),
    url(r'^/u/(?P<display_name>[A-Za-z0-9_])/edit/$',
        'remo.profiles.views.edit', name='profiles_edit'),

    url(r'^people/me/$', 'remo.profiles.views.view_my_profile',
        name='profiles_view_my_profile'),
    url(r'^people/invite/$', 'remo.profiles.views.invite',
        name='profiles_invite'),
    url(r'^people/', 'remo.profiles.views.list_profiles',
        name='profiles_list_profiles'),

    # browserid
    url(r'^browserid/', include('django_browserid.urls')),

    # login / logout
    url(r'^login/plain/$', 'remo.profiles.views.plainlogin',
        {'template_name':'plainlogin.html'}, name='plainlogin'),
    url(r'^logout/$', 'django.contrib.auth.views.logout',
        {'next_page':'/'}, name="logout"),
)

## In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
