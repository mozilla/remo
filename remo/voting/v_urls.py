from django.conf.urls import url

from remo.voting import views


urlpatterns = [
    url(r'^(?P<slug>[a-z0-9-]+)/edit/$', views.edit_voting, name='voting_edit_voting'),
    url(r'^(?P<slug>[a-z0-9-]+)/$', views.view_voting, name='voting_view_voting'),
    url(r'^(?P<slug>[a-z0-9-]+)/delete/$', views.delete_voting, name='voting_delete_voting'),
    url(r'^(?P<slug>[a-z0-9-]+)/comment/(?P<display_name>[A-Za-z0-9_]+)'
        r'/(?P<comment_id>\d+)/delete/$',
        views.delete_poll_comment, name='voting_delete_poll_comment'),
]
