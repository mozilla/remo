from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^$', 'remo.dashboard.views.dashboard', name='dashboard'),
    url(r'^emailmentees/$', 'remo.dashboard.views.email_mentees',
        name='email_mentees'),
    url(r'^stats/$', 'remo.dashboard.views.stats_dashboard',
        name='stats_dashboard'),
)
