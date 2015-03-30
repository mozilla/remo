from django.conf.urls import patterns, url

urlpatterns = patterns(
    'remo.voting.views',
    url(r'^$', 'list_votings', name='voting_list_votings'),
    url(r'^past_votings$', 'list_votings_past', name='voting_list_votings_past'),
    url(r'^new/$', 'edit_voting', name='voting_new_voting'),
)
