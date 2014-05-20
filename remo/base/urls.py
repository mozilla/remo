from django.conf.urls import include, patterns, url
from django.views.generic import TemplateView


urlpatterns = patterns(
    '',
    url(r'^browserid/', include('django_browserid.urls')),
    url(r'dashboard/$', 'remo.base.views.dashboard', name='dashboard'),
    url(r'dashboard/emailmentees/$', 'remo.base.views.email_mentees',
        name='email_mentees'),
    url(r'about/$', TemplateView.as_view(template_name='about.html'),
        name='about'),
    url(r'faq/$', TemplateView.as_view(template_name='faq.html'),
        name='faq'),
    url(r'labs/$', TemplateView.as_view(template_name='labs.html'),
        name='labs'),
    url(r'^$', 'remo.base.views.main', name='main'),
    url(r'stats/$', 'remo.base.views.stats_dashboard', name='stats_dashboard'),
)
