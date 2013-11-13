from django.conf.urls.defaults import patterns, url

# Old reporting system
urlpatterns = patterns(
    'remo.reports.views',
    url(r'^mentor/(?P<mentor>[A-Za-z0-9_]+)/$', 'list_reports',
        name='reports_list_mentor_reports'),
    url(r'^rep/(?P<rep>[A-Za-z0-9_]+)/$', 'list_reports',
        name='reports_list_rep_reports'),
    url(r'^$', 'list_reports', name='reports_list_reports'),
)

# New Generation reporting system
urlpatterns += patterns(
    'remo.reports.views',
    url(r'^new/$', 'edit_ng_report', name='reports_new_ng_report'),
)
