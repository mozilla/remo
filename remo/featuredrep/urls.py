from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^$', 'remo.featuredrep.views.list_featured',
        name='featuredrep_list_featured'),
    url(r'^add/$', 'remo.featuredrep.views.edit_featured',
        name='featuredrep_add_featured'),
    url(r'^edit/(?P<feature_id>\d+)/$',
        'remo.featuredrep.views.edit_featured',
        name='featuredrep_edit_featured'),
    url(r'^delete/(?P<feature_id>\d+)/$',
        'remo.featuredrep.views.delete_featured',
        name='featuredrep_delete_featured'),
)
