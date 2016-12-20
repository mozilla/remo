from django.conf.urls import url

from remo.dashboard import views as dashboard_views

urlpatterns = [
    url(r'^$', dashboard_views.dashboard, name='dashboard'),
    url(r'^emailmentees/$', dashboard_views.email_mentees, name='email_mentees'),
    url(r'^stats/$', dashboard_views.stats_dashboard, name='stats_dashboard'),
    url(r'^kpi/$', dashboard_views.kpi, name='kpi'),
]
