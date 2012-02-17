from django.contrib import messages
from django.shortcuts import redirect, render

import utils
from remo.featuredrep.models import FeaturedRep


def main(request):
    """Main page of the website."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    return render(request, 'main.html', {'featuredrep': featured_rep})


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
