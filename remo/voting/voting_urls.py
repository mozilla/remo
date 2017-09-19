from django.conf.urls import url

from remo.voting import views

urlpatterns = [
    url(r'^$', views.list_votings, name='voting_list_votings'),
    url(r'^new/$', views.edit_voting, name='voting_new_voting'),
]
