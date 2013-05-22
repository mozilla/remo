from datetime import date, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_control, never_cache

from django_browserid.auth import default_username_algo
from funfactory.helpers import urlparams
from product_details import product_details

import forms

from remo.base.decorators import permission_check
from remo.events.utils import get_events_for_user
from remo.featuredrep.models import FeaturedRep
from remo.profiles.models import UserProfile
from remo.profiles.models import FunctionalArea
from remo.reports.utils import REPORTS_PERMISSION_LEVEL, get_reports_for_year

USERNAME_ALGO = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)


@never_cache
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

    def date_joined_form_validation(form):
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
                                          instance=user.userprofile)
    datejoinedform = forms.ChangeDateJoinedForm(request.POST,
                                                instance=user.userprofile)

    if (userform.is_valid() and profileform.is_valid() and
        date_joined_form_validation(datejoinedform)):
        userform.save()
        profileform.save()

        if request.user.has_perm('profiles.can_edit_profiles'):
            # Update date joined
            datejoinedform.save()

            # Update groups.
            groups = {'Mentor': 'mentor_group',
                      'Admin': 'admin_group',
                      'Council': 'council_group',
                      'Rep': 'rep_group'}

            for group_db, group_html in groups.items():
                if request.POST.get(group_html, None):
                    user.groups.add(Group.objects.get(name=group_db))
                else:
                    user.groups.remove(Group.objects.get(name=group_db))

        messages.success(request, 'Profile successfully edited.')

        if request.user == user:
            return redirect('profiles_view_my_profile')
        else:
            redirect_url = reverse('profiles_view_profile',
                                   kwargs={'display_name':
                                           user.userprofile.display_name})
            return redirect(redirect_url)

    group_bits = map(lambda x: user.groups.filter(name=x).exists(),
                     ['Admin', 'Council', 'Mentor', 'Rep'])

    pageuser = get_object_or_404(User, userprofile__display_name=display_name)

    return render(request, 'profiles_edit.html',
                  {'userform': userform,
                   'profileform': profileform,
                   'datejoinedform': datejoinedform,
                   'pageuser': pageuser,
                   'group_bits': group_bits,
                   'range_years': range(1950, datetime.today().year - 11)})


def redirect_list_profiles(request):
    profiles_url = reverse('profiles_list_profiles')
    extra_path = '/' + request.path_info[len(profiles_url):]
    return redirect(urlparams(profiles_url, hash=extra_path), permanent=True)


@cache_control(private=True)
def list_profiles(request):
    """List users in Rep Group."""
    countries = product_details.get_regions('en').values()
    countries.sort()

    reps = (User.objects
            .filter(userprofile__registration_complete=True, groups__name='Rep')
            .order_by('userprofile__country', 'last_name', 'first_name'))

    return render(request, 'profiles_people.html',
                  {'countries': countries,
                   'reps': reps,
                   'areas': FunctionalArea.objects.all()})


@cache_control(private=True, max_age=60*5)
def view_profile(request, display_name):
    """View user profile."""
    user = get_object_or_404(User,
                             userprofile__display_name__iexact=display_name)
    if not user.groups.filter(name='Rep').exists():
        raise Http404

    if (not user.userprofile.registration_complete and
        not request.user.has_perm('profiles.can_edit_profiles')):
            raise Http404

    usergroups = user.groups.filter(Q(name='Mentor') | Q(name='Council'))
    data = {'pageuser': user,
            'user_profile': user.userprofile,
            'added_by': user.userprofile.added_by,
            'mentor': user.userprofile.mentor,
            'usergroups': usergroups}

    today = date.today()
    if ((request.user.is_authenticated() and
         user in request.user.mentees.all()) or
        user == request.user):
        reports = get_reports_for_year(
            user, start_year=2011, end_year=today.year,
            permission=REPORTS_PERMISSION_LEVEL['owner'])
    elif request.user.is_authenticated():
        reports = get_reports_for_year(
            user, start_year=2011, end_year=today.year,
            permission=REPORTS_PERMISSION_LEVEL['authenticated'])
    else:
        reports = get_reports_for_year(
            user, start_year=2011, end_year=today.year,
            permission=REPORTS_PERMISSION_LEVEL['anonymous'])

    past_user_events = get_events_for_user(user, to_date=today)
    data['monthly_reports'] = reports
    data['future_events'] = get_events_for_user(user, from_date=today)
    data['past_events'] = past_user_events.reverse()[:10]
    data['featured_rep'] = FeaturedRep.objects.filter(user=user)

    return render(request, 'profiles_view.html', data)


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

    return render(request, 'profiles_invite.html', {'form': form})


@permission_check(permissions=['profiles.can_delete_profiles'])
def delete_user(request, display_name):
    """Delete a user."""
    user = get_object_or_404(User, userprofile__display_name=display_name)

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User was deleted.')

    return redirect('main')
