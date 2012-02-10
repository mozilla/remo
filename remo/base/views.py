from django.shortcuts import render
from session_csrf import anonymous_csrf

from remo.featuredrep.models import FeaturedRep

@anonymous_csrf
def main(request):
    try:
        featured_rep = FeaturedRep.objects.latest()
    except FeaturedRep.DoesNotExist:
        featured_rep = None
    # You should use get_object_or_404 instead of using a try/except

    return render(request, 'main.html', {'featuredrep': featured_rep})
