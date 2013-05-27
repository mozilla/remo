from datetime import date, datetime

from django import http
from django_browserid import get_audience, verify
from django_browserid.auth import default_username_algo
from django_browserid.forms import BrowserIDForm
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.shortcuts import redirect, render
from django.template import Context, RequestContext, loader
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.http import require_POST

import forms
import utils

from remo.base.decorators import permission_check
from remo.base.mozillians import is_vouched, BadStatusCodeError
from remo.events.models import Event
from remo.featuredrep.models import FeaturedRep
from remo.remozilla.models import Bug
from remo.reports.models import Report
from remo.reports.utils import get_mentee_reports_for_month
from remo.reports.utils import REPORTS_PERMISSION_LEVEL, get_reports_for_year

USERNAME_ALGO = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)


@never_cache
@require_POST
def mozilla_browserid_verify(request):
    """
    Custom BrowserID verifier for ReMo users
    and vouched mozillians.
    """
    form = BrowserIDForm(request.POST)
    if form.is_valid():
        assertion = form.cleaned_data['assertion']
        audience = get_audience(request)
        result = verify(assertion, audience)
        try:
            _is_valid_login = False
            if result:
                if User.objects.filter(email=result['email']).exists():
                    _is_valid_login = True
                else:
                    data = is_vouched(result['email'])
                    if data and data['is_vouched']:
                        _is_valid_login = True
                        user = User.objects.create_user(
                            username=USERNAME_ALGO(data['email']),
                            email=data['email'])

                        first_name, last_name = (
                            data['full_name'].split(' ', 1)
                            if ' ' in data['full_name']
                            else ('', data['full_name']))
                        user.first_name = first_name
                        user.last_name = last_name
                        user.save()
                        user.groups.add(Group.objects.get(name='Mozillians'))

            if _is_valid_login:
                user = auth.authenticate(assertion=assertion,
                                         audience=audience)
                auth.login(request, user)
                return redirect('dashboard')

        except BadStatusCodeError:
            message = ('Email (%s) authenticated but unable to '
                       'connect to Mozillians to see if you are vouched' %
                       result['email'])
            return login_failed(request, message)

    return redirect(settings.LOGIN_REDIRECT_URL_FAILURE)


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

    # Mozillians block
    if user.groups.filter(name='Mozillians').exists():
        interestform = forms.TrackFunctionalAreasForm(
            request.POST or None, instance=user.userprofile)
        if request.method == 'POST' and interestform.is_valid():
            interestform.save()
            messages.success(request, 'Interests successfully saved')
            return redirect('dashboard')

        # Get the reps who match the specified interests
        interests = user.userprofile.tracked_functional_areas.all()
        tracked_interests = {}
        reps_reports = {}
        reps_past_events = {}
        reps_current_events = {}
        now = datetime.now()
        for interest in interests:
            # Get the Reps with the specified interest
            reps = User.objects.filter(groups__name='Rep').filter(
                userprofile__functional_areas=interest)
            tracked_interests[interest] = reps
            # Get the reports of the Reps with the specified interest
            reps_reports[interest] = Report.objects.filter(
                user__in=reps).order_by('created_on')[:20]
            # Get the events with the specified category
            events = Event.objects.filter(categories=interest)
            reps_past_events[interest] = events.filter(start__lt=now)[:50]
            reps_current_events[interest] = events.filter(start__gt=now)
        args['interestform'] = interestform
        args['reps_reports'] = reps_reports
        args['reps_past_events'] = reps_past_events
        args['reps_current_events'] = reps_current_events
        args['tracked_interests'] = tracked_interests
        return render(request, 'dashboard_mozillians.html', args)

    # Reps block
    q_closed = Q(status='RESOLVED') | Q(status='VERIFIED')
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
    my_mentees = User.objects.filter(userprofile__mentor=user,
                                     userprofile__registration_complete=True)

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
        args['email_mentees_form'] = forms.EmailUsersForm(my_mentees)

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

    return render(request, 'dashboard_reps.html', args)


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
        t.render(Context({'MEDIA_URL': settings.MEDIA_URL,
                          'request': request,
                          'user': request.user})))


def login_failed(request, msg=None):
    """Login failed view.

    This view acts like a segway between a failed login attempt and
    'main' view. Adds messages in the messages framework queue, that
    informs user login failed.

    """
    if not msg:
        msg = ('Login failed. Please make sure that you are '
               'an accepted Rep or a vouched Mozillian '
               'and you use your Bugzilla email to login.')
    messages.warning(request, msg)

    return redirect('main')


@permission_check(group='Mentor')
def email_mentees(request):
    """Email my mentees view."""
    if request.method == 'POST':
        my_mentees = User.objects.filter(userprofile__mentor=request.user)
        email_form = forms.EmailUsersForm(my_mentees, request.POST)
        if email_form.is_valid():
            email_form.send_mail(request)
        else:
            messages.error(request, 'Email not sent. Invalid data.')

    return redirect('dashboard')


@never_cache
@permission_check()
def edit_settings(request):
    """Edit user settings."""
    user = request.user
    form = forms.EditSettingsForm(request.POST or None,
                                  instance=user.userprofile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Settings successfully edited.')
        return redirect('dashboard')
    return render(request, 'settings.html', {'user': user,
                                             'settingsform': form})
