from django.conf.urls.defaults import *

# We use /people/[query] to automatically load the people list view
# and search for query. There are two reserved urls, r'/people/me/?'
# and r'/people/invite/?' which we want to point to
# 'profiles_view_my_profile' and 'profiles_invite' accordingly. If a
# user hits these urls without a trailing / we redirect him
# permanently to the url with the trailing slash, to avoid reaching
# the people list view with 'me' or 'invite' as a search term.
urlpatterns = patterns('',
    url(r'^invite/$', 'remo.profiles.views.invite', name='profiles_invite'),
    url(r'^invite$', 'django.views.generic.simple.redirect_to',
        {'url': 'invite/', 'permanent': True}),
    url(r'^$', 'remo.profiles.views.list_profiles',
        name='profiles_list_profiles'),
    # This url is intentionally left without a $
    url(r'^', 'remo.profiles.views.redirect_list_profiles',
        name='profiles_list_profiles_redirect'),
)
