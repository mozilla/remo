from datetime import date

from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import redirect, render
from django.template import Context, RequestContext, loader
from django.views.decorators.cache import cache_control, never_cache

from django_arecibo.tasks import post

import utils
from remo.base.decorators import permission_check
from remo.featuredrep.models import FeaturedRep
from remo.remozilla.models import Bug
from remo.reports.models import Report
from remo.reports.utils import get_mentee_reports_for_month
from remo.reports.utils import get_reports_for_year


@cache_control(private=True, no_cache=True)
def main(request):
    """Main page of the website."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    return render(request, 'main.html', {'featuredrep': featured_rep,
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
    mentorship_requests = Bug.objects.filter(component='Mentorship')
    mentorship_requests = mentorship_requests.exclude(status='RESOLVED')
    cit_requests = Bug.objects.filter(component='Community IT Requests')
    cit_requests = cit_requests.exclude(status='RESOLVED')
    planning_requests = Bug.objects.filter(component='Planning')
    planning_requests = planning_requests.exclude(status='RESOLVED')

    today = date.today()
    monthly_reports = get_reports_for_year(user, start_year=2011,
                                           end_year=today.year,
                                           private=False)

    my_q = (Q(cc=user) | Q(creator=user))
    my_q_assigned = (my_q | Q(assigned_to=user))
    my_mentees = User.objects.filter(userprofile__mentor=user)

    my_budget_requests = budget_requests.filter(my_q)
    my_swag_requests = swag_requests.filter(my_q)

    if user.groups.filter(name='Mentor').exists():
        mentees_budget_requests = (budget_requests.
                                   filter(creator__in=my_mentees))
        mentees_swag_requests = swag_requests.filter(creator__in=my_mentees)
        my_mentorship_requests = mentorship_requests.filter(my_q)
        my_mentorship_requests = my_mentorship_requests.order_by('whiteboard')
        mentees_reports_list = (Report.objects.filter(mentor=user).
                                order_by('-created_on')[:20])
        mentees_reports_grid = get_mentee_reports_for_month(user)

    else:
        mentees_budget_requests = None
        mentees_swag_requests = None
        my_mentorship_requests = None
        mentees_reports_list = None
        mentees_reports_grid = None

    if user.groups.filter(Q(name='Admin') | Q(name='Council')).exists():
        all_budget_requests = budget_requests.all()[:20]
        all_swag_requests = swag_requests.all()[:20]
        my_cit_requests = cit_requests
        my_planning_requests = planning_requests
        all_reports = Report.objects.all().order_by('-created_on')[:20]
    else:
        all_budget_requests = None
        all_swag_requests = None
        my_cit_requests = None
        my_planning_requests = planning_requests.filter(my_q_assigned)
        all_reports = None

    if user.groups.filter(name='Admin').exists():
        reps = User.objects.filter(groups__name="Rep")
        reps_without_mentors = reps.filter(
            userprofile__registration_complete=True, userprofile__mentor=None)
        reps_without_profile = reps.filter(
            userprofile__registration_complete=False)
    else:
        reps_without_mentors = None
        reps_without_profile = None

    return render(request, 'dashboard.html',
                  {'my_budget_requests': my_budget_requests,
                   'mentees_budget_requests': mentees_budget_requests,
                   'all_budget_requests': all_budget_requests,
                   'my_swag_requests': my_swag_requests,
                   'mentees_swag_requests': mentees_swag_requests,
                   'all_swag_requests': all_swag_requests,
                   'my_cit_requests': my_cit_requests,
                   'my_mentorship_requests': my_mentorship_requests,
                   'my_planning_requests': my_planning_requests,
                   'reps_without_profile': reps_without_profile,
                   'reps_without_mentors': reps_without_mentors,
                   'monthly_reports': monthly_reports,
                   'mentees_reports_list': mentees_reports_list,
                   'mentees_reports_grid': mentees_reports_grid,
                   'all_reports': all_reports})


def custom_404(request):
    """Custom 404 error handler."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    t = loader.get_template('404.html')
    post(request, 404)
    return http.HttpResponseNotFound(
        t.render(RequestContext(request, {'request_path': request.path,
                                          'featuredrep': featured_rep})))


def custom_500(request):
    """Custom 500 error handler."""
    t = loader.get_template('500.html')
    uid = post(request, 500)
    return http.HttpResponseServerError(
        t.render(Context({'MEDIA_URL': settings.MEDIA_URL,
                          'request': request,
                          'user': request.user,
                          'uid': uid})))


def login_failed(request):
    """Login failed view.

    This view acts like a segway between a failed login attempt and
    'main' view. Adds messages in the messages framework queue, that
    informs user login failed.

    """
    messages.warning(request, ('Login failed. Please make sure that you are '
                               'an accepted Rep and you use your Bugzilla '
                               'email to login.'))

    return redirect('main')
