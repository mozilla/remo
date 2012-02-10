from datetime import datetime

import django.db
from django.conf import settings
from django.contrib.auth.views import login as django_login
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404, redirect, render

from django_browserid.auth import default_username_algo

from remo.base.decorators import permission_check
from remo.base.countries import COUNTRIES

import forms

USERNAME_ALGO = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)


@permission_check(permissions=['profiles.can_edit_profiles'],
                  display_name_field='display_name')
def edit(request, display_name):
    """ Edit user profile.

    Permission to edit user profile is granted to the user who owns
    the profile and all the users with permissions to edit profiles.
    """
    user = get_object_or_404(User, userprofile__display_name=display_name)

    if request.method == 'POST':
        userform = forms.ChangeUserForm(request.POST, instance=user)
        profileform = forms.ChangeProfileForm(request.POST,
                                              instance=user.userprofile)

        if userform.is_valid() and profileform.is_valid():
            userform.save()
            profileform.save()

            if request.user.has_perm('profiles.can_edit_profiles'):
                if request.POST.get('mentor_group', None):
                    user.groups.add(Group.objects.get(name="Mentor"))
                else:
                    user.groups.remove(Group.objects.get(name="Mentor"))

                if request.POST.get('admin_group', None):
                    user.groups.add(Group.objects.get(name="Admin"))
                else:
                    user.groups.remove(Group.objects.get(name="Admin"))

                if request.POST.get('council_group', None):
                    user.groups.add(Group.objects.get(name="Council"))
                else:
                    user.groups.remove(Group.objects.get(name="Council"))

                if request.POST.get('rep_group', None):
                    user.groups.add(Group.objects.get(name="Rep"))
                else:
                    user.groups.remove(Group.objects.get(name="Rep"))

            messages.success(request, 'Profile successfully edited')
            return redirect('profiles_view_my_profile')
    else:
        userform = forms.ChangeUserForm(instance=user)
        profileform = forms.ChangeProfileForm(instance=user.userprofile)

    group_bits = map(lambda x: user.groups.filter(name=x).count() > 0,
                     ['Admin', 'Council', 'Mentor', 'Rep'])

    mentors = User.objects.filter(userprofile__registration_complete=True,
                                  groups__name="Mentor")

    return render(request, "profiles_edit.html",
                  {'userform': userform,
                   'profileform': profileform,
                   'pageuser': user,
                   'group_bits': group_bits,
                   'mentors': mentors,
                   'countries': COUNTRIES,
                   'range_years': range(1950, datetime.today().year - 11)})


def list_profiles(request):
    """ List users in Rep Group. """
    return render(request, 'profiles_people.html',
                  {'people': User.objects.\
                   filter(userprofile__registration_complete=True,
                          groups__name="Rep")})


def view_profile(request, display_name):
    """ View user profile """
    user = get_object_or_404(User, userprofile__display_name=display_name)
    return render(request, 'profiles_view.html', {'pageuser': user})


@permission_check()
def view_my_profile(request):
    """ View logged-in user profile. """
    return view_profile(request,
                        display_name=request.user.userprofile.display_name)


@permission_check(permissions=['profiles.create_user'])
def invite(request):
    """ Invite a user. """
    if request.POST:
        form = forms.InviteUserForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                # Django does not require unique emails but we do.
                if User.objects.filter(email=email).count():
                    raise django.db.IntegrityError

                user = User.objects.create_user(username=USERNAME_ALGO(email),
                                                email=email)
                user.userprofile.added_by = request.user
                user.userprofile.save()
            except django.db.IntegrityError:
                messages.error(request, 'User already exists')
            else:
                messages.success(request, 'User was successfuly invited, '
                                 'now shoot some mails!')
                return redirect('profiles_invite')

    else:
        form = forms.InviteUserForm()

    return render(request, "profiles_invite.html",
                  {'form': form}
                  )


@permission_check(permissions=['profiles.can_edit_profiles'])
def delete_user(request, display_name):
    """ Delete a user. """
    user = get_object_or_404(User, userprofile__display_name=display_name)

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User was deleted')

    return redirect('main')


def plainlogin(request, template_name):
    """ Login without BrowserID. """
    return django_login(request, template_name=template_name)
