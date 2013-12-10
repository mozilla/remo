from django.conf.urls.defaults import patterns, url

# Old reporting system
urlpatterns = patterns(
    'remo.reports.views',
    url(r'^(?P<year>\d+)/(?P<month>\w+)/$', 'view_report',
        name='reports_view_report'),
    url(r'^(?P<year>\d+)/(?P<month>\w+)/edit/$', 'edit_report',
        name='reports_edit_report'),
    url(r'^(?P<year>\d+)/(?P<month>\w+)/delete/$',
        'delete_report', name='reports_delete_report'),
    url(r'^(?P<year>\d+)/(?P<month>\w+)/delete/comment/(?P<comment_id>\d+)/$',
        'delete_report_comment', name='reports_delete_report_comment'),
)

# New Generation reporting system
urlpatterns += patterns(
    'remo.reports.views',
    url(r'^(?P<year>\d+)/(?P<month>\w+)/(?P<day>\d+)/(?P<id>\d+)/$',
        'view_ng_report', name='reports_ng_view_report'),
    url(r'^(?P<year>\d+)/(?P<month>\w+)/(?P<day>\d+)/(?P<id>\d+)/edit/$',
        'edit_ng_report', name='reports_ng_edit_report'),
    url(r'^(?P<year>\d+)/(?P<month>\w+)/(?P<day>\d+)/(?P<id>\d+)/delete/$',
        'delete_ng_report', name='reports_ng_delete_report'),
    url((r'^(?P<year>\d+)/(?P<month>\w+)/(?P<day>\d+)/(?P<id>\d+)'
        '/comment/(?P<comment_id>\d+)/delete/$'),
        'delete_ng_report_comment', name='reports_ng_delete_report_comment'),
)
