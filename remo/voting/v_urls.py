from django.conf.urls.defaults import *

urlpatterns = patterns('remo.voting.views',
    url(r'^(?P<slug>[a-z0-9-]+)/edit/$', 'edit_voting',
        name='voting_edit_voting'),
    url(r'^(?P<slug>[a-z0-9-]+)/$', 'view_voting',
        name='voting_view_voting')
)
