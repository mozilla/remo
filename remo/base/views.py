from django import http
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import redirect, render
from django.template import Context, RequestContext, loader
from django.views.decorators.cache import never_cache

import utils
from remo.base.decorators import permission_check
from remo.featuredrep.models import FeaturedRep
from remo.remozilla.models import Bug


@never_cache
def main(request):
    """Main page of the website."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    if featured_rep:
        avatar_url = featured_rep.user.userprofile.get_avatar_url(80)
    else:
        avatar_url = None
    return render(request, 'main.html', {'featuredrep': featured_rep,
                                         'avatar_url': avatar_url,
                                         'next_url': reverse('dashboard')})


@never_cache
@permission_check()
def dashboard(request):
    """Dashboard view."""
    user = request.user
    budget_requests = Bug.objects.filter(component='Budget Requests')
    budget_requests = budget_requests.exclude(status='RESOLVED')
    swag_requests = Bug.objects.filter(component='Swag Requests')
    swag_requests = swag_requests.exclude(status='RESOLVED')


    my_budget_requests = budget_requests.filter((Q(cc=user)|
                                                 Q(creator=user)))
    my_swag_requests = swag_requests.filter((Q(cc=user)|
                                                 Q(creator=user)))

    if user.groups.filter(name="Mentor").exists():
        mentees_budget_requests = budget_requests.filter(
            creator=user.mentees.all)
        mentees_swag_requests = swag_requests.filter(
            creator=user.mentees.all)
    else:
        mentees_budget_requests = None
        mentees_swag_requests = None

    if user.groups.filter(Q(name="Admin")|Q(name="Council")).exists():
        all_budget_requests = budget_requests.all()[:20]
        all_swag_requests = swag_requests.all()[:20]
        cit_requests = Bug.objects.filter(component='Community IT Requests')

    else:
        all_budget_requests = None
        all_swag_requests = None
        cit_requests = None

    return render(request, 'dashboard.html',
                  {'my_budget_requests': my_budget_requests,
                   'mentees_budget_requests': mentees_budget_requests,
                   'all_budget_requests': all_budget_requests,
                   'my_swag_requests': my_swag_requests,
                   'mentees_swag_requests': mentees_swag_requests,
                   'all_swag_requests': all_swag_requests,
                   'cit_requests': cit_requests})


def custom_404(request):
    """Custom 404 error handler."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    if featured_rep:
        avatar_url = featured_rep.user.userprofile.get_avatar_url(80)
    else:
        avatar_url = None
    t = loader.get_template('404.html')
    return http.HttpResponseNotFound(
        t.render(RequestContext(request, {'request_path': request.path,
                                          'featuredrep': featured_rep,
                                          'avatar_url': avatar_url})))


def custom_500(request):
    """Custom 500 error handler."""
    t = loader.get_template('500.html')
    return http.HttpResponseServerError(
        t.render(Context({'MEDIA_URL': settings.MEDIA_URL,
                          'request': request,
                          'user': request.user})))


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
