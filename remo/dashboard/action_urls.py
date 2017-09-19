from django.conf.urls import url

from remo.dashboard import views


# Action items urls
urlpatterns = [
    url(r'^$', views.list_action_items, name='list_action_items'),
]
