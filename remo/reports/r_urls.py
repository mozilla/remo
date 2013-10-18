from django.conf.urls.defaults import patterns, url

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
