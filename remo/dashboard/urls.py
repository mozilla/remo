from django.views.generic import RedirectView
from django.conf.urls import url

from remo.dashboard import views as dashboard_views

urlpatterns = [
    url(r'^$', dashboard_views.dashboard, name='dashboard'),
    url(r'^emailmentees/$', dashboard_views.email_mentees, name='email_mentees'),
    url(r'^stats/$', RedirectView.as_view(url='/dashboard/kpi/', permanent=True)),
    url(r'^kpi/$', dashboard_views.kpi, name='kpi'),
]
