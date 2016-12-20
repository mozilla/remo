from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve as serve_view

from remo.base import views as base_views
from remo.profiles import views as profiles_views


# Monkeypatch log_settings
import log_settings  # noqa

handler404 = base_views.custom_404
handler500 = base_views.custom_500
robots_txt = base_views.robots_txt

urlpatterns = [
    # 'me' urls
    url(r'^me/$', profiles_views.view_my_profile, name='profiles_view_my_profile'),
    # Profiles
    url(r'^u/', include('remo.profiles.user_urls')),
    url(r'^people/', include('remo.profiles.people_urls')),
    # Events
    url(r'^e/', include('remo.events.e_urls')),
    url(r'^events/', include('remo.events.event_urls')),
    # Reports
    url(r'^reports/', include('remo.reports.report_urls')),
    # Featuredrep
    url(r'^featured/', include('remo.featuredrep.urls')),
    # Login
    url(r'oidc/', include('mozilla_django_oidc.urls')),
    # API
    url(r'^api/', include('remo.api.urls')),
    url(r'^', include('remo.base.urls')),
    # Dashboard
    url(r'^dashboard/', include('remo.dashboard.urls')),
    # Action Items
    url(r'^actions/', include('remo.dashboard.action_urls')),
    # Admin
    url(r'^admin/', include(admin.site.urls)),
    # Voting
    url(r'^voting/', include('remo.voting.voting_urls')),
    url(r'^v/', include('remo.voting.v_urls')),
    # Portal base content
    url(r'^content/', include('remo.base.content_urls')),
    # Portal settings
    url(r'^settings/', include('remo.base.settings_urls')),
    # Generate a robots.txt
    url(r'^robots\.txt$', robots_txt),
    # contribute.json url
    url(r'^(?P<path>contribute\.json)$', serve_view, {'document_root': settings.ROOT}),
]


if settings.DEBUG:
    urlpatterns += [
        url(r'^404/$', handler404, name='404'),
        url(r'^500/$', handler500, name='500')
    ]
    urlpatterns += staticfiles_urlpatterns()
