from django import http
from django_browserid import BrowserIDException, get_audience, verify
from django_browserid.auth import default_username_algo
from django_browserid.views import Verify
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.timezone import now
from django.views import generic
from django.views.decorators.cache import cache_control, never_cache

from django_statsd.clients import statsd

import forms
import utils

from remo.base.decorators import PermissionMixin, permission_check
from remo.base.forms import EmailMentorForm
from remo.base.mozillians import BadStatusCodeError, is_vouched
from remo.base.utils import get_date
from remo.events.models import Event
from remo.featuredrep.models import FeaturedRep
from remo.profiles.forms import UserStatusForm
from remo.profiles.models import UserProfile, UserStatus
from remo.remozilla.models import Bug
from remo.reports.models import NGReport


USERNAME_ALGO = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)


class BrowserIDVerify(Verify):

    def login_failure(self, error=None, message=None):
        """Custom login failed method.

        This method acts like a segway between a failed login attempt and
        'main' view. Adds messages in the messages framework queue, that
        informs user login failed.

        """
        if not message:
            message = ('Login failed. Please make sure that you are '
                       'an accepted Rep or a vouched Mozillian '
                       'and you use your Bugzilla email to login.')
        messages.warning(self.request, message)

        return super(BrowserIDVerify, self).login_failure(error=error)

    def form_valid(self, form):
        """
        Custom BrowserID verifier for ReMo users
        and vouched mozillians.
        """
        self.assertion = form.cleaned_data['assertion']
        self.audience = get_audience(self.request)
        result = verify(self.assertion, self.audience)
        _is_valid_login = False

        if result:
            if User.objects.filter(email=result['email']).exists():
                _is_valid_login = True
            else:
                try:
                    data = is_vouched(result['email'])
                except BadStatusCodeError:
                    msg = ('Email (%s) authenticated but unable to '
                           'connect to Mozillians to see if you are vouched' %
                           result['email'])
                    return self.login_failure(message=msg)

                if data and data['is_vouched']:
                    _is_valid_login = True
                    user = User.objects.create_user(
                        username=USERNAME_ALGO(data['email']),
                        email=data['email'])
                    # Due to privacy settings, this might be missing
                    if 'full_name' not in data:
                        data['full_name'] = 'Anonymous Mozillian'
                    else:
                        user.userprofile.mozillian_username = data['username']
                        user.userprofile.save()

                    first_name, last_name = (
                        data['full_name'].split(' ', 1)
                        if ' ' in data['full_name']
                        else ('', data['full_name']))
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()
                    user.groups.add(
                        Group.objects.get(name='Mozillians'))

            if _is_valid_login:
                try:
                    self.user = auth.authenticate(assertion=self.assertion,
                                                  audience=self.audience)
                    auth.login(self.request, self.user)
                except BrowserIDException as e:
                    return self.login_failure(error=e)

                if self.request.user and self.request.user.is_active:
                    return self.login_success()

        return self.login_failure()


@cache_control(private=True, no_cache=True)
def main(request):
    """Main page of the website."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    return render(request, 'main.html', {'featuredrep': featured_rep})


def dashboard_mozillians(request, user):
    args = {}
    user_profile = user.userprofile
    interestform = forms.TrackFunctionalAreasForm(request.POST or None,
                                                  instance=user_profile)
    reps_email_form = forms.EmailRepsForm(request.POST or None)
    if interestform.is_valid():
        interestform.save()
        messages.success(request, 'Interests successfully saved')
        return redirect('dashboard')
    if reps_email_form.is_valid():
        functional_area = reps_email_form.cleaned_data['functional_area']
        reps = (User.objects
                .filter(groups__name='Rep')
                .filter(userprofile__functional_areas=functional_area))
        reps_email_form.send_email(request, reps)
        return redirect('dashboard')

    # Get the reps who match the specified interests
    interests = user.userprofile.tracked_functional_areas.all()
    tracked_interests = {}
    reps_past_events = {}
    reps_current_events = {}
    reps_ng_reports = {}
    today = now().date()
    unavailable_rep_exists = {}

    for interest in interests:
        # Get the Reps with the specified interest
        reps = User.objects.filter(groups__name='Rep').filter(
            userprofile__functional_areas=interest)
        tracked_interests[interest.name] = {
            'id': interest.id, 'reps': reps}

        # Get the reports of the Reps with the specified interest
        ng_reports = NGReport.objects.filter(report_date__lte=today,
                                             functional_areas=interest,
                                             user__in=reps)
        reps_ng_reports[interest.name] = (ng_reports
                                          .order_by('-report_date')[:10])

        # Get the events with the specified category
        events = Event.objects.filter(categories=interest)
        reps_past_events[interest.name] = events.filter(start__lt=now())[:50]
        reps_current_events[interest.name] = events.filter(start__gte=now())

        # Check if there is an unavailable Rep for the specific interest
        unavailable_val = reps.filter(
            userprofile__is_unavailable=True).exists()
        unavailable_rep_exists[interest.name] = unavailable_val

    args['unavailable_rep_exists'] = unavailable_rep_exists
    args['reps_ng_reports'] = reps_ng_reports
    args['interestform'] = interestform
    args['reps_past_events'] = reps_past_events
    args['reps_current_events'] = reps_current_events
    args['tracked_interests'] = tracked_interests
    args['reps_email_form'] = reps_email_form
    return render(request, 'dashboard_mozillians.html', args)


@never_cache
@permission_check()
def dashboard(request):
    """Dashboard view."""
    user = request.user
    args = {}

    # Mozillians block
    if user.groups.filter(name='Mozillians').exists():
        return dashboard_mozillians(request, user)

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

    today = now().date()
    # NG Reports
    if user.groups.filter(name='Rep').exists():
        args['ng_reports'] = (user.ng_reports
                              .filter(report_date__lte=today)
                              .order_by('-report_date'))
        args['today'] = now()

    # Dashboard data
    my_q = (Q(cc=user) | Q(creator=user))
    my_q_assigned = (my_q | Q(assigned_to=user))
    my_mentees = User.objects.filter(userprofile__mentor=user,
                                     userprofile__registration_complete=True)

    args['my_budget_requests'] = budget_requests.filter(my_q).distinct()
    args['my_swag_requests'] = swag_requests.filter(my_q).distinct()

    if user.groups.filter(name='Mentor').exists():
        args['mentees_ng_reportees'] = User.objects.filter(
            ng_reports__isnull=False, ng_reports__mentor=user).distinct()
        args['mentees_budget_requests'] = (budget_requests.
                                           filter(creator__in=my_mentees).
                                           distinct())
        args['mentees_swag_requests'] = (swag_requests.
                                         filter(creator__in=my_mentees).
                                         distinct())
        my_mentorship_requests = mentorship_requests.filter(my_q_assigned)
        my_mentorship_requests = my_mentorship_requests.order_by('whiteboard')
        args['my_mentorship_requests'] = my_mentorship_requests.distinct()
        args['mentees_emails'] = (
            my_mentees.values_list('first_name', 'last_name', 'email') or
            None)
        args['email_mentees_form'] = forms.EmailUsersForm(my_mentees)

    if user.groups.filter(Q(name='Admin') | Q(name='Council')).exists():
        args['all_budget_requests'] = budget_requests.all()[:20]
        args['all_swag_requests'] = swag_requests.all()[:20]
        args['my_cit_requests'] = cit_requests
        args['my_planning_requests'] = planning_requests
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
    return http.HttpResponseNotFound(render(request, '404.html',
                                            {'featuredrep': featured_rep}))


def custom_500(request):
    """Custom 500 error handler."""
    return http.HttpResponseServerError(render(request, '500.html'))


def robots_txt(request):
    """Generate a robots.txt.

    Do not allow bots to crawl report pages (bug 923754).
    """
    robots = 'User-agent: *\n'

    if settings.ENGAGE_ROBOTS:
        robots += 'Disallow: /reports/\n'
        users = User.objects.filter(groups__name='Rep',
                                    userprofile__registration_complete=True)
        for user in users:
            robots += ('Disallow: /u/{display_name}/r/\n'
                       .format(display_name=user.userprofile.display_name))
    else:
        robots += 'Disallow: /\n'

    return http.HttpResponse(robots, mimetype='text/plain')


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


def stats_dashboard(request):
    """Stats dashboard view."""
    reps = User.objects.filter(groups__name='Rep',
                               userprofile__registration_complete=True)

    q_active = Q(
        ng_reports__report_date__range=[get_date(weeks=-4), get_date(weeks=4)])
    q_inactive = Q(
        ng_reports__report_date__range=[get_date(weeks=-8), get_date(weeks=8)])

    active = reps.filter(q_active)
    inactive_low = reps.filter(q_inactive & ~q_active)
    inactive_high = reps.filter(~q_inactive)

    args = {}
    args['active_users'] = active.distinct().count()
    args['inactive_low_users'] = inactive_low.distinct().count()
    args['inactive_high_users'] = inactive_high.distinct().count()
    args['reps'] = reps.count()
    args['past_events'] = Event.objects.filter(start__lt=now()).count()
    args['future_events'] = Event.objects.filter(start__gte=now()).count()
    args['activities'] = NGReport.objects.all().count()

    return render(request, 'stats_dashboard.html', args)


@never_cache
@permission_check()
def edit_settings(request):
    """Edit user settings."""
    user = request.user
    form = forms.EditSettingsForm(request.POST or None,
                                  instance=user.userprofile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        for field in form.changed_data:
            statsd.incr('base.edit_setting_%s' % field)
        messages.success(request, 'Settings successfully edited.')
        return redirect('dashboard')
    return render(request, 'settings.html', {'user': user,
                                             'settingsform': form})


@never_cache
@permission_check(permissions=['profiles.add_userstatus',
                               'profiles.change_userstatus'],
                  filter_field='display_name', owner_field='user',
                  model=UserProfile)
def edit_availability(request, display_name):
    """Edit availability settings."""

    user = request.user
    args = {}
    created = False

    if user.userprofile.is_unavailable:
        status = UserStatus.objects.filter(user=user).latest('created_on')
    else:
        status = UserStatus(user=user)
        created = True

    initial_data = {'is_replaced': False}
    if not created:
        initial_data['expected_date'] = (status.expected_date
                                         .strftime('%d %B %Y'))
    status_form = UserStatusForm(request.POST or None,
                                 instance=status,
                                 initial=initial_data)
    email_mentor_form = EmailMentorForm(request.POST or None)

    if status_form.is_valid():
        status_form.save()

        if created and email_mentor_form.is_valid():
            expected_date = status_form.cleaned_data['expected_date']
            msg = email_mentor_form.cleaned_data['body']
            subject = ('[Rep unavailable] Mentee %s will be unavailable '
                       'from %s' % (request.user.get_full_name(),
                                    expected_date.strftime('%d %B %Y')))
            template = 'emails/mentor_unavailability_notification.txt'

            subject = ('[Mentee %s] Mentee will be unavailable '
                       'until %s' % (request.user.get_full_name(),
                                     expected_date.strftime('%d %B %Y')))
            email_mentor_form.send_email(request, subject, msg, template,
                                         {'user_status': status})
        messages.success(request, 'Request submitted successfully.')
        return redirect('dashboard')

    args['status_form'] = status_form
    args['email_form'] = email_mentor_form
    args['created'] = created
    return render(request, 'edit_availability.html', args)


class BaseListView(PermissionMixin, generic.ListView):
    """Base content list view."""
    template_name = 'base_content_list.html'
    create_object_url = None

    def get_context_data(self, **kwargs):
        context = super(BaseListView, self).get_context_data(**kwargs)
        context['verbose_name'] = self.model._meta.verbose_name
        context['verbose_name_plural'] = self.model._meta.verbose_name_plural
        context['create_object_url'] = self.create_object_url
        return context


class BaseCreateView(PermissionMixin, generic.CreateView):
    """Base content create view."""
    template_name = 'base_content_edit.html'

    def get_context_data(self, **kwargs):
        context = super(BaseCreateView, self).get_context_data(**kwargs)
        context['verbose_name'] = self.model._meta.verbose_name
        context['creating'] = True
        return context

    def form_valid(self, form):
        content = self.model._meta.verbose_name.capitalize()
        messages.success(self.request, '%s succesfully created.' % content)
        return super(BaseCreateView, self).form_valid(form)


class BaseUpdateView(PermissionMixin, generic.UpdateView):
    """Base content edit view."""
    template_name = 'base_content_edit.html'

    def get_context_data(self, **kwargs):
        context = super(BaseUpdateView, self).get_context_data(**kwargs)
        context['verbose_name'] = self.model._meta.verbose_name
        context['creating'] = False
        return context

    def form_valid(self, form):
        content = self.model._meta.verbose_name.capitalize()
        messages.success(self.request, '%s succesfully updated.' % content)
        return super(BaseUpdateView, self).form_valid(form)

    def get(self, request, *args, **kwargs):
        if getattr(self.get_object(), 'is_editable', True):
            return super(BaseUpdateView, self).get(request, *args, **kwargs)
        messages.error(self.request, 'Object cannot be updated.')
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        if getattr(self.get_object(), 'is_editable', True):
            return super(BaseUpdateView, self).post(request, *args, **kwargs)
        messages.error(self.request, 'Object cannot be updated.')
        return redirect(self.success_url)


class BaseDeleteView(PermissionMixin, generic.DeleteView):
    """Base content delete view."""

    def delete(self, request, *args, **kwargs):
        """Override delete method to show message."""
        if getattr(self.get_object(), 'is_editable', True):
            content = self.model._meta.verbose_name.capitalize()
            messages.success(self.request, '%s succesfully deleted.' % content)
            return super(BaseDeleteView, self).delete(request, *args, **kwargs)
        messages.error(self.request, 'Object cannot be deleted.')
        return redirect(self.success_url)
