from django.shortcuts import render
from session_csrf import anonymous_csrf

from remo.featuredrep.models import FeaturedRep

import utils


def main(request):
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    return render(request, 'main.html', {'featuredrep': featured_rep})
