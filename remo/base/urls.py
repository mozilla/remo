from django.conf.urls import url
from django.views.generic import TemplateView

from remo.base import views as base_views

urlpatterns = [
    url(r'about/$', TemplateView.as_view(template_name='about.jinja'), name='about'),
    url(r'faq/$', TemplateView.as_view(template_name='faq.jinja'), name='faq'),
    url(r'^$', base_views.main, name='main'),
    url(r'^capture-csp-violation$', base_views.capture_csp_violation,
        name='capture-csp-violation'),
]
