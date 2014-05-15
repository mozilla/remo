from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'remo.voting.views',
    url(r'^$', 'list_votings', name='voting_list_votings'),
    url(r'^past/$', 'list_votings_archive', {'period': 'past'},
        name='voting_list_past_votings'),
    url(r'^new/$', 'edit_voting', name='voting_new_voting'),
)
