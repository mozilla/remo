from datetime import datetime

import django.db
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.views import login as django_login
from django.views.generic.simple import direct_to_template
from session_csrf import anonymous_csrf
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from django_browserid.auth import default_username_algo
from remo.base.decorators import permission_check
from remo.base.countries import COUNTRIES
# alphabetize imports

import forms

# capitalize constant
username_algo = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)


@permission_check(permissions=['profiles.can_edit_profiles'],
                  display_name_field='display_name')
def edit(request, display_name):
    # Missing comment
    user = get_object_or_404(User, userprofile__display_name = display_name)

    if request.method == 'POST':
        userform = forms.ChangeUserForm(request.POST, instance=user)
        profileform = forms.ChangeProfileForm(request.POST, instance=user.userprofile)

        if userform.is_valid() and profileform.is_valid():
            userform.save()
            profileform.save()

            if request.user.has_perm('profiles.can_edit_profiles'):
                if request.POST.get('mentor_group', None):
                    user.groups.add(Group.objects.get(name="Mentor"))
                    # get rid of line breaks in conditions that are paired.
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
                   'range_years': range(1950,
                                        datetime.today().year-11)}
                  )


def list_profiles(request):
    # Missing comment
    return render(request, 'profiles_people.html',
                  {'people': User.objects.\
                   filter(userprofile__registration_complete=True,
                          groups__name="Rep")
                   }) # move this up to after "Rep)"


def view_profile(request, display_name):
    # Missing comment
    user = get_object_or_404(User, userprofile__display_name = display_name)
    return render(request, 'profiles_view.html', {'pageuser': user})


@permission_check(permissions=['profiles.create_user'])
def invite(request):
    # Missing comment
    if request.POST:
        form = forms.InviteUserForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                # django does not required unique emails but we do
                if User.objects.filter(email=email).count():
                    raise django.db.IntegrityError

                user = User.objects.create_user(username=username_algo(email),
                                                email=email)
                user.userprofile.added_by = request.user
                user.userprofile.save()

            except django.db.IntegrityError:
                messages.error(request, 'User already exists')

            else:
                messages.success(request, 'User was successfuly invited, now shoot some mails!')
                return redirect('profiles_invite')

    else:
        form = forms.InviteUserForm()

    return render(request, "profiles_invite.html",
                  {'form': form}
                  )


@permission_check(permissions=['profiles.can_edit_profiles'])
def delete_user(request, display_name):
    # Missing comment
    user = get_object_or_404(User, userprofile__display_name=display_name)

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User was deleted')

    return redirect('main')


@permission_check()
def view_my_profile(request):
    # Missing comment
    return view_profile(request,
                        display_name=request.user.userprofile.display_name)


def plainlogin(request, template_name):
    # Missing comment
    return django_login(request, template_name=template_name)


