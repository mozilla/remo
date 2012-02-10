from django.shortcuts import render
from session_csrf import anonymous_csrf

from remo.featuredrep.models import FeaturedRep

@anonymous_csrf
# You don't need to call anonymous_csrf if you are using the latest playdoh.
# You can set ANON_ALWAYS = True in settings in base.py
def main(request):
    try:
        featured_rep = FeaturedRep.objects.latest()

    except FeaturedRep.DoesNotExist:
        featured_rep = None
    # You should use get_object_or_404 instead of using a try/except

    return render(request, 'main.html', {'featuredrep': featured_rep})
    # If you are wrapping content, make sure it is consistent. Some of these are
    # like {'featuredrep': featured_rep} and some are like { 'featuredrep': featured_rep }
    # I noticed some are one or the other but just choose one style and use it throughout.
