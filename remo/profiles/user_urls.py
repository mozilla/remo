from django.conf.urls import include, url

from remo.profiles import views

urlpatterns = [
    url(r'^(?P<display_name>[A-Za-z0-9_]+)/$', views.view_profile, name='profiles_view_profile'),
    url(r'^(?P<display_name>[A-Za-z0-9_]+)/edit/$', views.edit, name='profiles_edit'),
    url(r'^(?P<display_name>[A-Za-z0-9_]+)/delete/$', views.delete_user, name='profiles_delete'),
    url(r'^(?P<display_name>[A-Za-z0-9_]+)/r/', include('remo.reports.r_urls'))
]
