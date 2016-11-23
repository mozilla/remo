import json
import logging

from django import http
from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views import generic
from django.views.decorators.cache import cache_control, never_cache

from django_statsd.clients import statsd
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
from raven.contrib.django.models import client

import forms
import utils
from remo.base.decorators import PermissionMixin, permission_check
from remo.base.forms import EmailMentorForm
from remo.featuredrep.models import FeaturedRep
from remo.profiles.forms import UserStatusForm
from remo.profiles.models import UserProfile, UserStatus


class OIDCCallbackView(OIDCAuthenticationCallbackView):

    def login_failure(self, msg=''):
        if not msg:
            msg = ('Login failed. Please make sure that you are '
                   'an accepted Rep or a vouched Mozillian '
                   'and you use your Bugzilla email to login.')
        messages.warning(self.request, msg)
        return super(OIDCCallbackView, self).login_failure()


@cache_control(private=True, no_cache=True)
def main(request):
    """Main page of the website."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    return render(request, 'main.jinja', {'featuredrep': featured_rep})


def custom_404(request):
    """Custom 404 error handler."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    return http.HttpResponseNotFound(render(request, '404.jinja',
                                            {'featuredrep': featured_rep}))


def custom_500(request):
    """Custom 500 error handler."""
    return http.HttpResponseServerError(render(request, '500.jinja'))


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

    return http.HttpResponse(robots, content_type='text/plain')


@never_cache
@permission_check()
def edit_settings(request):
    """Edit user settings."""
    user = request.user
    if user.groups.filter(name='Mozillians').exists():
        raise Http404

    form = forms.EditSettingsForm(request.POST or None,
                                  instance=user.userprofile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        for field in form.changed_data:
            statsd.incr('base.edit_setting_%s' % field)
        messages.success(request, 'Settings successfully edited.')
        return redirect('dashboard')
    return render(request, 'settings.jinja', {'user': user,
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

    if user.groups.filter(Q(name='Mozillians') | Q(name='Alumni')).exists():
        raise Http404()

    try:
        status = (UserStatus.objects.filter(user=user)
                  .filter(is_unavailable=True).latest('created_on'))
    except UserStatus.DoesNotExist:
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
            expected_date = (status_form.cleaned_data['expected_date']
                             .strftime('%d %B %Y'))
            start_date = (status_form.cleaned_data['start_date']
                          .strftime('%d %B %Y'))
            msg = email_mentor_form.cleaned_data['body']
            mentee = request.user.get_full_name()
            template = 'emails/mentor_unavailability_notification.jinja'

            subject = ('[Mentee {0}] Mentee will be unavailable starting '
                       'on {1} until {2}'.format(mentee,
                                                 start_date,
                                                 expected_date))
            email_mentor_form.send_email(request, subject, msg, template,
                                         {'user_status': status})
        messages.success(request, 'Request submitted successfully.')
        return redirect('dashboard')

    args['status_form'] = status_form
    args['email_form'] = email_mentor_form
    args['created'] = created
    return render(request, 'edit_availability.jinja', args)


class BaseListView(PermissionMixin, generic.ListView):
    """Base content list view."""
    template_name = 'base_content_list.jinja'
    create_object_url = None

    def get_context_data(self, **kwargs):
        context = super(BaseListView, self).get_context_data(**kwargs)
        context['verbose_name'] = self.model._meta.verbose_name
        context['verbose_name_plural'] = self.model._meta.verbose_name_plural
        context['create_object_url'] = self.create_object_url
        return context


class BaseCreateView(PermissionMixin, generic.CreateView):
    """Base content create view."""
    template_name = 'base_content_edit.jinja'

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
    template_name = 'base_content_edit.jinja'

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


@require_POST
@csrf_exempt
def capture_csp_violation(request):
    data = client.get_data_from_request(request)
    data.update({
        'level': logging.INFO,
        'logger': 'CSP',
    })
    try:
        csp_data = json.loads(request.body)
    except ValueError:
        # Cannot decode CSP violation data, ignore
        return HttpResponseBadRequest('Invalid CSP Report')

    try:
        blocked_uri = csp_data['csp-report']['blocked-uri']
    except KeyError:
        # Incomplete CSP report
        return HttpResponseBadRequest('Incomplete CSP Report')

    client.captureMessage(
        message='CSP Violation: {}'.format(blocked_uri),
        data=data)

    return HttpResponse('Captured CSP violation, thanks for reporting.')
