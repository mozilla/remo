from datetime import date

from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, render
from django.template import Context, RequestContext, loader
from django.views.decorators.cache import cache_control, never_cache

from django_arecibo.tasks import post

import utils

from remo.base.decorators import permission_check
from remo.base.forms import EmailMenteesForm
from remo.base.tasks import send_mail_task
from remo.featuredrep.models import FeaturedRep
from remo.remozilla.models import Bug
from remo.reports.models import Report
from remo.reports.utils import get_mentee_reports_for_month
from remo.reports.utils import REPORTS_PERMISSION_LEVEL, get_reports_for_year


@cache_control(private=True, no_cache=True)
def main(request):
    """Main page of the website."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    return render(request, 'main.html', {'featuredrep': featured_rep})


@never_cache
@permission_check()
def dashboard(request):
    """Dashboard view."""
    user = request.user
    args = {}
    q_closed = Q(status='RESOLVED')| Q(status='VERIFIED')
    budget_requests = (Bug.objects.filter(component='Budget Requests').
                       exclude(q_closed))
    swag_requests = (Bug.objects.filter(component='Swag Requests').
                     exclude(q_closed))
    mentorship_requests = (Bug.objects.filter(component='Mentorship').
                           exclude(q_closed))
    cit_requests = (Bug.objects.filter(component='Community IT Requests').
                    exclude(q_closed))
    planning_requests = (Bug.objects.filter(component='Planning').
                         exclude(q_closed))

    today = date.today()
    if user.groups.filter(name='Rep').exists():
        args['monthly_reports'] = get_reports_for_year(
            user, start_year=2011, end_year=today.year,
            permission=REPORTS_PERMISSION_LEVEL['owner'])

    my_q = (Q(cc=user) | Q(creator=user))
    my_q_assigned = (my_q | Q(assigned_to=user))
    my_mentees = User.objects.filter(userprofile__mentor=user)

    args['my_budget_requests'] = budget_requests.filter(my_q).distinct()
    args['my_swag_requests'] = swag_requests.filter(my_q).distinct()

    if user.groups.filter(name='Mentor').exists():
        args['mentees_budget_requests'] = (budget_requests.
                                           filter(creator__in=my_mentees).
                                           distinct())
        args['mentees_swag_requests'] = (swag_requests.
                                         filter(creator__in=my_mentees).
                                         distinct())
        my_mentorship_requests = mentorship_requests.filter(my_q_assigned)
        my_mentorship_requests = my_mentorship_requests.order_by('whiteboard')
        args['my_mentorship_requests'] = my_mentorship_requests.distinct()
        args['mentees_reports_list'] = (Report.objects.filter(mentor=user).
                                        order_by('-created_on').
                                        distinct()[:20])
        args['mentees_reports_grid'] = get_mentee_reports_for_month(user)
        args['mentees_emails'] = (
            my_mentees.values_list('first_name', 'last_name', 'email') or
            None)
        args['email_mentees_form'] = EmailMenteesForm(
            initial={'email_of_mentor': user.email})

    if user.groups.filter(Q(name='Admin') | Q(name='Council')).exists():
        args['all_budget_requests'] = budget_requests.all()[:20]
        args['all_swag_requests'] = swag_requests.all()[:20]
        args['my_cit_requests'] = cit_requests
        args['my_planning_requests'] = planning_requests
        args['all_reports'] = Report.objects.all().order_by('-created_on')[:20]
    else:
        args['my_planning_requests'] = (planning_requests.
                                        filter(my_q_assigned).
                                        distinct())

    if user.groups.filter(name='Admin').exists():
        args['is_admin'] = True
        reps = User.objects.filter(groups__name='Rep')
        args['reps_without_mentors'] = reps.filter(
            userprofile__registration_complete=True, userprofile__mentor=None)
        args['reps_without_profile'] = reps.filter(
            userprofile__registration_complete=False)

    return render(request, 'dashboard.html', args)


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


@permission_check(permissions=['profiles.create_user'])
def email_mentees(request):
    """Email my mentees view."""
    if request.method == 'POST':
        email_form = EmailMenteesForm(request.POST)
        if email_form.is_valid():
            from_email = '%s <%s>' % (request.user.get_full_name(),
                                      request.user.email)
            mentees = (User.objects.filter(userprofile__mentor=request.user).
                       values_list('email', flat=True))
            send_mail_task.delay(sender=from_email,
                                 recipients=mentees,
                                 subject=email_form.cleaned_data['subject'],
                                 message=email_form.cleaned_data['body'])
            messages.success(request, 'Email sent successfully.')
        else:
            messages.error(request, 'Email not sent. Invalid data.')

    return redirect('dashboard')
