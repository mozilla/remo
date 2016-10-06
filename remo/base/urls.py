from django.conf.urls import patterns, url
from django.views.generic import TemplateView


urlpatterns = patterns(
    '',
    url(r'about/$', TemplateView.as_view(template_name='about.jinja'),
        name='about'),
    url(r'faq/$', TemplateView.as_view(template_name='faq.jinja'),
        name='faq'),
    url(r'labs/$', TemplateView.as_view(template_name='labs.jinja'),
        name='labs'),
    url(r'^$', 'remo.base.views.main', name='main'),
    # CSP violations
    url(r'^capture-csp-violation$', 'remo.base.views.capture_csp_violation',
        name='capture-csp-violation'),
)
