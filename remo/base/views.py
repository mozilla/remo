from django.shortcuts import render

import utils
from remo.featuredrep.models import FeaturedRep


def main(request):
    """Main page of the website."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    return render(request, 'main.html', {'featuredrep': featured_rep})
