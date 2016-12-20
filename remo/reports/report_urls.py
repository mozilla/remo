from django.conf.urls import url

from remo.reports import views

FUNCTIONAL_AREA_REGEX = 'functional-area/(?P<functional_area_slug>.+)'


# New Generation reporting system
urlpatterns = [
    url(r'^new/$', views.edit_ng_report, name='reports_new_ng_report'),
    url(r'^mentor/(?P<mentor>\w+)/$', views.list_ng_reports, name='list_ng_reports_mentor'),
    url(r'^rep/(?P<rep>\w+)/$', views.list_ng_reports, name='list_ng_reports_rep'),
    url(r'^rep/(?P<rep>\w+)/%s/$' % FUNCTIONAL_AREA_REGEX, views.list_ng_reports,
        name='list_ng_reports_rep_functional_area'),
    url(r'^mentor/(?P<mentor>\w+)/%s/$' % FUNCTIONAL_AREA_REGEX, views.list_ng_reports,
        name='list_ng_reports_mentor_functional_area'),
    url(r'^%s/$' % FUNCTIONAL_AREA_REGEX, views.list_ng_reports,
        name='list_ng_reports_functional_area'),
    url(r'^$', views.list_ng_reports, name='list_ng_reports'),
]
