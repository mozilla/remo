from django import http
from django.conf import settings
from django.shortcuts import render
from django.template import Context, RequestContext, loader

import utils
from remo.featuredrep.models import FeaturedRep


def main(request):
    """Main page of the website."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    return render(request, 'main.html', {'featuredrep': featured_rep})


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
