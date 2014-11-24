from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from funfactory.monkeypatches import patch
patch()

# funfactory puts the more limited CompressorExtension extension in
# but we need the one from jingo_offline_compressor.jinja2ext otherwise we
# might an error like this:
#
#    AttributeError: 'CompressorExtension' object has no attribute 'nodelist'
#
from jingo_offline_compressor.jinja2ext import CompressorExtension
import jingo
try:
    jingo.env.extensions.pop(
        'compressor.contrib.jinja2ext.CompressorExtension'
    )
except KeyError:
    # happens if the urlconf is loaded twice
    pass
jingo.env.add_extension(CompressorExtension)


handler404 = 'remo.base.views.custom_404'
handler500 = 'remo.base.views.custom_500'
robots_txt = 'remo.base.views.robots_txt'

admin.autodiscover()

urlpatterns = patterns(
    '',

    # 'me' urls
    url(r'^me/$', 'remo.profiles.views.view_my_profile',
        name='profiles_view_my_profile'),

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
    url(r'^contribute\.json$', 'remo.base.views.contribute_json'),
)


if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^404/$', handler404, name='404'),
        url(r'^500/$', handler500, name='500'))
    urlpatterns += staticfiles_urlpatterns()
