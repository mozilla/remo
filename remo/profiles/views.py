from datetime import date, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_control, never_cache

from django_browserid.auth import default_username_algo
from product_details import product_details

import forms
from remo.base.decorators import permission_check
from remo.remozilla.tasks import fetch_bugs
from remo.reports.utils import REPORTS_PERMISSION_LEVEL, get_reports_for_year

USERNAME_ALGO = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)


@never_cache
@permission_check(permissions=['profiles.can_edit_profiles'],
                  display_name_field='display_name')
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

    if request.method == 'POST':
        userform = forms.ChangeUserForm(request.POST, instance=user)
        profileform = forms.ChangeProfileForm(request.POST,
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
    else:
        userform = forms.ChangeUserForm(instance=user)
        profileform = forms.ChangeProfileForm(instance=user.userprofile)
        datejoinedform = forms.ChangeDateJoinedForm(instance=user.userprofile)

    group_bits = map(lambda x: user.groups.filter(name=x).exists(),
                     ['Admin', 'Council', 'Mentor', 'Rep'])

    pageuser = get_object_or_404(User, userprofile__display_name=display_name)

    countries = product_details.get_regions('en').values()
    countries.sort()

    return render(request, 'profiles_edit.html',
                  {'userform': userform,
                   'profileform': profileform,
                   'datejoinedform': datejoinedform,
                   'pageuser': pageuser,
                   'group_bits': group_bits,
                   'countries': countries,
                   'range_years': range(1950, datetime.today().year - 11)})


@cache_control(private=True, max_age=60*10)
def list_profiles(request):
    """List users in Rep Group."""
    return render(request, 'profiles_people.html',
                  {'people': User.objects.\
                   filter(userprofile__registration_complete=True,
                          groups__name='Rep').order_by('userprofile__country',
                                                       'last_name',
                                                       'first_name')})


@cache_control(private=True, max_age=60*5)
def view_profile(request, display_name):
    """View user profile."""
    user = get_object_or_404(User,
                             userprofile__display_name__iexact=display_name)
    usergroups = user.groups.filter(Q(name='Mentor')|Q(name='Council'))

    data = {'pageuser': user,
            'user_profile': user.userprofile,
            'added_by': user.userprofile.added_by,
            'mentor': user.userprofile.mentor,
            'usergroups': usergroups}

    if user.groups.filter(name='Rep').exists():
        today = date.today()
        if (request.user.groups.filter(name='Admin').exists() or
            (request.user.is_authenticated() and
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

        data['monthly_reports'] = reports

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
    if request.POST:
        form = forms.InviteUserForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.create_user(username=USERNAME_ALGO(email),
                                            email=email)
            user.userprofile.added_by = request.user
            user.userprofile.save()

            # Fetch bugs from day 0 to correlate new user with bugs.
            fetch_bugs.delay(days=10000)

            messages.success(request, ('User was successfully invited, '
                                       'now shoot some mails!'))
            return redirect('profiles_invite')

    else:
        form = forms.InviteUserForm()

    return render(request, 'profiles_invite.html', {'form': form})


@permission_check(permissions=['profiles.can_edit_profiles'])
def delete_user(request, display_name):
    """Delete a user."""
    user = get_object_or_404(User, userprofile__display_name=display_name)

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User was deleted')

    return redirect('main')
