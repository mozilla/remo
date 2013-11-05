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
        'ng_view_report', name='ng_reports_view_report'),
    url(r'^(?P<year>\d+)/(?P<month>\w+)/(?P<day>\d+)/(?P<id>\d+)/edit/$',
        'ng_edit_report', name='ng_reports_edit_report'),
    url(r'^delete/(?P<id>\d+)$', 'ng_delete_report',
        name='ng_reports_delete_report'),
    url((r'^(?P<year>\d+)/(?P<month>\w+)/d(?P<day>\d+)/'
         '(?P<id>\d+)/delete/comment/(?P<comment_id>\d+)/$'),
        'ng_delete_report_comment', name='ng_reports_delete_report_comment'),
)
