from django import http
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.template import Context, RequestContext, loader
from django.views.decorators.cache import never_cache

import utils
from remo.featuredrep.models import FeaturedRep


@never_cache
def main(request):
    """Main page of the website."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    if featured_rep:
        avatar_url = featured_rep.user.userprofile.get_avatar_url(80)
    else:
        avatar_url = None
    return render(request, 'main.html', {'featuredrep': featured_rep,
                                         'avatar_url': avatar_url})


def custom_404(request):
    """Custom 404 error handler."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    t = loader.get_template('404.html')
    return http.HttpResponseNotFound(
        t.render(RequestContext(request, {'request_path': request.path,
                                          'featuredrep': featured_rep})))


def custom_500(request):
    """Custom 500 error handler."""
    t = loader.get_template('500.html')
    return http.HttpResponseServerError(
        t.render(Context({'MEDIA_URL': settings.MEDIA_URL})))


def login_failed(request):
    """Login failed view.

    This view acts like a segway between a failed login attempt and
    'main' view. Adds messages in the messages framework queue, that
    informs user login failed.

    """
    messages.warning(request, ("Login failed. Please make sure that you are "
                               "an accepted Rep and you use your Bugzilla "
                               "email to login."))

    return redirect('main')
