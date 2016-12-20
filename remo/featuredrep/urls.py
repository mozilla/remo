from django.conf.urls import url

from remo.featuredrep import views

urlpatterns = [
    url(r'^$', views.list_featured, name='featuredrep_list_featured'),
    url(r'^add/$', views.edit_featured, name='featuredrep_add_featured'),
    url(r'^edit/(?P<feature_id>\d+)/$', views.edit_featured, name='featuredrep_edit_featured'),
    url(r'^delete/(?P<feature_id>\d+)/$', views.delete_featured,
        name='featuredrep_delete_featured'),
]
