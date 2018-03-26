from django.conf.urls import url
from django.views.generic import RedirectView

from remo.profiles import views as profiles_views
# We use /people/[query] to automatically load the people list view
# and search for query. There are other reserved urls, which we want to point to
# other views accordingly. If a user hits these urls without a trailing / we
# redirect them permanently to the url with the trailing slash, to avoid reaching
# the people list view with e.g. 'invite' as a search term.
urlpatterns = [
    url(r'^invite/$', profiles_views.invite, name='profiles_invite'),
    url(r'^invite$', RedirectView.as_view(url='invite/', permanent=True)),
    url(r'^alumni/$', profiles_views.list_alumni, name='profiles_alumni'),
    url(r'^alumni$', RedirectView.as_view(url='alumni/', permanent=True)),
    url(r'^mentors/$', profiles_views.list_mentors, name='profiles_list_mentors'),
    url(r'^mentors$', RedirectView.as_view(url='mentors/', permanent=True)),
    url(r'^$', profiles_views.list_profiles, name='profiles_list_profiles'),
    # This url is intentionally left without a $
    url(r'^', profiles_views.redirect_list_profiles, name='profiles_list_profiles_redirect'),
]
