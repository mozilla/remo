from django.conf.urls.defaults import *

urlpatterns = patterns('remo.reports.views',
    # This url is intentionally left without a $
    url(r'^', 'list_reports', name='reports_list_reports'),
)
