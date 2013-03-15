from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin

from funfactory.monkeypatches import patch
patch()

handler404 = 'remo.base.views.custom_404'
handler500 = 'remo.base.views.custom_500'

admin.autodiscover()

urlpatterns = patterns('',
    # 'me' urls
    url(r'^me/$', 'remo.profiles.views.view_my_profile',
        name='profiles_view_my_profile'),
    url(r'^me/currentreport/$', 'remo.reports.views.current_report',
        name='reports_view_current_report'),
    url(r'^me/currentreport/edit/$', 'remo.reports.views.current_report',
        dict({'edit': True}), name='reports_edit_current_report'),

    # profiles
    url(r'^u/', include('remo.profiles.user_urls')),
    url(r'^people/', include('remo.profiles.people_urls')),

    # events
    url(r'^e/', include('remo.events.e_urls')),
    url(r'^events/', include('remo.events.event_urls')),

    # reports
    url(r'^reports/', include('remo.reports.report_urls')),

    # featuredrep
    url(r'^featured/', include('remo.featuredrep.urls')),

    # custom browserid
    url(r'', include('remo.base.urls')),

    # login / logout
    url(r'^login/failed/$',
        'remo.base.views.login_failed', name='login_failed'),
    url(r'^logout/$', 'django.contrib.auth.views.logout',
        {'next_page': '/'}, name='logout'),

    # API
    url(r'^api/', include('remo.api.urls')),

    url(r'^', include('remo.base.urls')),

    # Admin
    url(r'^admin/', include(admin.site.urls)),

    # Voting
    url(r'^votings/', include('remo.voting.voting_urls')),
    url(r'^v/', include('remo.voting.v_urls')),
)

## In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        url(r'^404/$', handler404, name='404'),
        url(r'^500/$', handler500, name='500'),
        url(r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
