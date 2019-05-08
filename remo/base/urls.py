from django.conf.urls import url

from remo.base import views as base_views

urlpatterns = [
    url(r'^$', base_views.main, name='main'),
    url(r'^capture-csp-violation$', base_views.capture_csp_violation,
        name='capture-csp-violation'),
]
