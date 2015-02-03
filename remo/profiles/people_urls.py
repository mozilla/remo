from django.conf.urls import patterns, url
from django.views.generic import RedirectView

# We use /people/[query] to automatically load the people list view
# and search for query. There are tree reserved urls, r'/people/me/?',
# r'/people/invite/?' and r'/people/alumni/?' which we want to point to
# 'profiles_view_my_profile, 'profiles_invite' and 'profiles_list_alumni'
# accordingly. If a user hits these urls without a trailing / we redirect him
# permanently to the url with the trailing slash, to avoid reaching
# the people list view with 'me' or 'invite' as a search term.
urlpatterns = patterns(
    '',
    url(r'^invite/$', 'remo.profiles.views.invite', name='profiles_invite'),
    url(r'^invite$', RedirectView.as_view(url='invite/', permanent=True)),
    url(r'^alumni$', RedirectView.as_view(url='alumni/', permanent=True)),
    url(r'^alumni/$', 'remo.profiles.views.list_alumni',
        name='profiles_alumni'),
    url(r'^$', 'remo.profiles.views.list_profiles',
        name='profiles_list_profiles'),
    # This url is intentionally left without a $
    url(r'^', 'remo.profiles.views.redirect_list_profiles',
        name='profiles_list_profiles_redirect'),
)
