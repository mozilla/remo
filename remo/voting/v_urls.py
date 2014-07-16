from django.conf.urls import patterns, url

urlpatterns = patterns(
    'remo.voting.views',
    url(r'^(?P<slug>[a-z0-9-]+)/edit/$', 'edit_voting',
        name='voting_edit_voting'),
    url(r'^(?P<slug>[a-z0-9-]+)/$', 'view_voting',
        name='voting_view_voting'),
    url(r'^(?P<slug>[a-z0-9-]+)/delete/$', 'delete_voting',
        name='voting_delete_voting'),
    url(r'^(?P<slug>[a-z0-9-]+)/comment/(?P<display_name>[A-Za-z0-9_]+)'
        '/(?P<comment_id>\d+)/delete/$',
        'delete_poll_comment', name='voting_delete_poll_comment'),
)
