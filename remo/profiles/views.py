from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.encoding import iri_to_uri
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_control, never_cache

import waffle
from django_statsd.clients import statsd
from mozilla_django_oidc.auth import default_username_algo
from product_details import product_details

import forms

from remo.base.decorators import permission_check
from remo.base.templatetags.helpers import urlparams
from remo.events.utils import get_events_for_user
from remo.profiles.models import UserProfile, UserStatus
from remo.profiles.models import FunctionalArea
from remo.voting.tasks import rotm_nomination_end_date

USERNAME_ALGO = getattr(settings, 'OIDC_USERNAME_ALGO', default_username_algo)


@never_cache
@user_passes_test(lambda u: u.groups.filter(Q(name='Rep') | Q(name='Admin')),
                  login_url=settings.LOGIN_REDIRECT_URL)
@permission_check(permissions=['profiles.can_edit_profiles'],
                  filter_field='display_name', owner_field='user',
                  model=UserProfile)
def edit(request, display_name):
    """Edit user profile.

    Permission to edit user profile is granted to the user who owns
    the profile and all the users with permissions to edit profiles.

    Argument display_name should be lowered before queries because we
    allow case-insensitive profile urls. E.g. both /u/Giorgos and
    /u/giorgos are the same person.

    """

    def profile_date_form_validation(form):
        """Convenience function to only validate datejoinedform when
        user has permissions.

        """
        if request.user.has_perm('profiles.can_edit_profiles'):
            if form.is_valid():
                return True
            return False
        return True

    user = get_object_or_404(User,
                             userprofile__display_name__iexact=display_name)

    userform = forms.ChangeUserForm(request.POST or None, instance=user)
    profileform = forms.ChangeProfileForm(request.POST or None,
                                          instance=user.userprofile,
                                          request=request)
    profile_date_form = forms.ChangeDatesForm(request.POST or None,
                                              instance=user.userprofile)

    if (userform.is_valid() and profileform.is_valid() and
            profile_date_form_validation(profile_date_form)):
        userform.save()
        profileform.save()

        if request.user.has_perm('profiles.can_edit_profiles'):
            # Update groups.
            groups = {'Mentor': 'mentor_group',
                      'Admin': 'admin_group',
                      'Council': 'council_group',
                      'Rep': 'rep_group',
                      'Alumni': 'alumni_group',
                      'Review': 'review_group',
                      'Peers': 'peers_group'}

            for group_db, group_html in groups.items():
                if Group.objects.filter(name=group_db).exists():
                    if request.POST.get(group_html, None):
                        user.groups.add(Group.objects.get(name=group_db))
                    else:
                        user.groups.remove(Group.objects.get(name=group_db))

            # Update date fields
            profile_date_form.save()

        messages.success(request, 'Profile successfully edited.')
        statsd.incr('profiles.edit_profile')

        if request.user == user:
            return redirect('profiles_view_my_profile')
        else:
            redirect_url = reverse('profiles_view_profile',
                                   kwargs={'display_name':
                                           user.userprofile.display_name})
            return redirect(redirect_url)
    else:
        # If forms are not valid and the fields are dirty, get a fresh copy
        # of the object.
        # This is needed when an invalid display_name is used.
        # Django tries to resolve the url based on this display_name, which
        # results in a NoReverseMatch error. See also bug:
        # https://bugzilla.mozilla.org/show_bug.cgi?id=1147541
        user = User.objects.get(pk=user.id)

    group_bits = map(lambda x: user.groups.filter(name=x).exists(),
                     ['Admin', 'Council', 'Mentor', 'Rep', 'Alumni', 'Review', 'Peers'])

    functional_areas = map(int, profileform['functional_areas'].value())
    user_is_alumni = user.groups.filter(name='Alumni').exists()

    return render(request, 'profiles_edit.jinja',
                  {'userform': userform,
                   'profileform': profileform,
                   'profile_date_form': profile_date_form,
                   'pageuser': user,
                   'group_bits': group_bits,
                   'range_years': range(1950, now().date().year - 11),
                   'functional_areas': functional_areas,
                   'user_is_alumni': user_is_alumni})


def redirect_list_profiles(request):
    profiles_url = reverse('profiles_list_profiles')
    extra_path = iri_to_uri('/' + request.path_info[len(profiles_url):])
    return redirect(urlparams(profiles_url, hash=extra_path), permanent=True)


@cache_control(private=True)
def list_profiles(request):
    """List users in Rep Group."""
    countries = product_details.get_regions('en').values()
    countries.sort()

    reps = (User.objects
            .filter(userprofile__registration_complete=True,
                    groups__name='Rep')
            .order_by('userprofile__country', 'last_name', 'first_name'))

    return render(request, 'profiles_people.jinja',
                  {'countries': countries,
                   'reps': reps,
                   'areas': FunctionalArea.objects.all()})


@cache_control(private=True, max_age=60 * 5)
def view_profile(request, display_name):
    """View user profile."""
    user = get_object_or_404(User,
                             userprofile__display_name__iexact=display_name)
    user_is_alumni = user.groups.filter(name='Alumni').exists()
    if not user.groups.filter(Q(name='Rep') | Q(name='Alumni')).exists():
        raise Http404

    if (not user.userprofile.registration_complete and
            not request.user.has_perm('profiles.can_edit_profiles')):
            raise Http404

    nominee_form = forms.RotmNomineeForm(request.POST or None,
                                         instance=user.userprofile)

    usergroups = user.groups.filter(Q(name='Mentor') | Q(name='Council'))
    is_nomination_period = now().date() < rotm_nomination_end_date()
    data = {'pageuser': user,
            'user_profile': user.userprofile,
            'added_by': user.userprofile.added_by,
            'mentor': user.userprofile.mentor,
            'usergroups': usergroups,
            'user_nominated': user.userprofile.is_rotm_nominee,
            'is_nomination_period': is_nomination_period,
            'user_is_alumni': user_is_alumni}

    if UserStatus.objects.filter(user=user, is_unavailable=True).exists():
        status = UserStatus.objects.filter(user=user).latest('created_on')
        data['user_status'] = status
        if user == request.user:
            today = now().date()
            date = (status.expected_date.strftime('%d %B %Y')
                    if status.expected_date > today else None)
            msg = render_to_string(
                'includes/view_profile_unavailable_msg.jinja',
                {'date': date,
                 'display_name': user.userprofile.display_name})
            messages.info(request, mark_safe(msg))

    if nominee_form.is_valid():
        if ((is_nomination_period or waffle.switch_is_active('enable_rotm_tasks')) and
                request.user.groups.filter(name='Mentor').exists() and request.user != user):
            nominee_form.save(nominated_by=request.user)
            return redirect('profiles_view_profile', display_name=display_name)

        messages.warning(request, ('Only mentors can nominate a mentee.'))

    if user_is_alumni:
        msg = render_to_string('includes/alumni_msg.jinja')
        messages.info(request, mark_safe(msg))

    today = now().date()

    # NGReports
    data['ng_reports'] = (user.ng_reports
                          .filter(report_date__lte=today)
                          .order_by('-report_date'))

    past_user_events = get_events_for_user(user, to_date=today)

    data['future_events'] = get_events_for_user(user, from_date=today)
    data['past_events'] = past_user_events.reverse()[:10]
    data['featured_rep'] = user.featuredrep_users.all()
    data['request_user'] = request.user
    data['nominee_form'] = nominee_form

    return render(request, 'profiles_view.jinja', data)


@permission_check()
def view_my_profile(request):
    """View logged-in user profile."""
    return view_profile(request,
                        display_name=request.user.userprofile.display_name)


@cache_control(private=True, no_cache=True)
@permission_check(permissions=['profiles.create_user'])
def invite(request):
    """Invite a user."""
    form = forms.InviteUserForm(request.POST or None)

    if form.is_valid():
        email = form.cleaned_data['email']
        user = User.objects.create_user(username=USERNAME_ALGO(email),
                                        email=email)
        # Add new users to Rep group
        user.groups.add(Group.objects.get(name='Rep'))

        if request.user.groups.filter(name='Mentor').exists():
            user.userprofile.mentor = request.user
        user.userprofile.added_by = request.user
        user.userprofile.save()

        messages.success(request, ('User was successfully invited, '
                                   'now shoot some mails!'))
        return redirect('profiles_invite')

    return render(request, 'profiles_invite.jinja', {'form': form})


@permission_check(permissions=['profiles.can_delete_profiles'])
def delete_user(request, display_name):
    """Delete a user."""
    user = get_object_or_404(User, userprofile__display_name=display_name)

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User was deleted.')
        statsd.incr('profiles.delete_profile')

    return redirect('main')


@cache_control(private=True)
def list_alumni(request):
    """List users in Alumni Group."""
    query = User.objects.filter(groups__name='Alumni')

    alumni_paginator = Paginator(query, settings.ITEMS_PER_PAGE)
    alumni_page = request.GET.get('page', 1)

    try:
        objects = alumni_paginator.page(alumni_page)
    except PageNotAnInteger:
        objects = alumni_paginator.page(1)
    except EmptyPage:
        objects = alumni_paginator.page(alumni_paginator.num_pages)

    return render(request, 'profiles_list_alumni.jinja', {'objects': objects})
