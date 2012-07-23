from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
    url(r'dashboard/$', 'remo.base.views.dashboard', name='dashboard'),
    url(r'dashboard/emailmentees/$', 'remo.base.views.email_mentees',
        name='email_mentees'),
    url(r'about/$', direct_to_template, {'template': 'about.html'},
        name='about'),
    url(r'faq/$', direct_to_template, {'template': 'faq.html'},
        name='faq'),
    url(r'labs/$', direct_to_template, {'template': 'labs.html'},
        name='labs'),
    url(r'^$', 'remo.base.views.main', name='main'),
)
