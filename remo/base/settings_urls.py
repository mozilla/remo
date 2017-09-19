from django.conf.urls import url

from remo.base import views

urlpatterns = [
    url(r'^$', views.edit_settings, name='edit_settings'),
    url(r'^availability/(?P<display_name>[A-Za-z0-9_]+)/$',
        views.edit_availability, name='edit_availability'),
]
