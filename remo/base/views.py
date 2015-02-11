from django import http
from django_browserid.http import JSONResponse
from django_browserid.views import Verify
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import generic
from django.views.decorators.cache import cache_control, never_cache

from django_statsd.clients import statsd

import forms
import utils
from remo.base.decorators import PermissionMixin, permission_check
from remo.base.forms import EmailMentorForm
from remo.featuredrep.models import FeaturedRep
from remo.profiles.forms import UserStatusForm
from remo.profiles.models import UserProfile, UserStatus


class BrowserIDVerify(Verify):

    def login_failure(self, msg=''):
        if not msg:
            msg = ('Login failed. Please make sure that you are '
                   'an accepted Rep or a vouched Mozillian '
                   'and you use your Bugzilla email to login.')
        messages.warning(self.request, msg)
        return JSONResponse({'redirect': self.failure_url})


@cache_control(private=True, no_cache=True)
def main(request):
    """Main page of the website."""
    featured_rep = utils.latest_object_or_none(FeaturedRep)
    return render(request, 'main.html', {'featuredrep': featured_rep})


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


def contribute_json(request):
    """Generate a contribute.json."""
    template = render(request, 'contribute.json')
    return http.HttpResponse(template, mimetype='application/json')


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

    if user.groups.filter(name='Mozillians').exists():
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
