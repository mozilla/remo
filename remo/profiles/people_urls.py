from django.conf.urls.defaults import *

urlpatterns = patterns('remo.profiles.views',
    url(r'^me/$', 'view_my_profile', name='profiles_view_my_profile'),
    url(r'^invite/$', 'invite', name='profiles_invite'),
    # This url is intentionally left without a $
    url(r'^', 'list_profiles', name='profiles_list_profiles'),
)
