from datetime import datetime

import django.db
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.views import login as django_login
from django.views.generic.simple import direct_to_template
from session_csrf import anonymous_csrf
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from django_browserid.auth import default_username_algo
from remo.base.decorators import permission_check

import forms

username_algo = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)


@anonymous_csrf
def main(request):
    return direct_to_template(request, template="main.html")


@login_required
def edit(request, display_name=None):
    return direct_to_template(request, template="profiles_edit.html")


def list_profiles(request):
    return render(request, 'profiles_people.html',
                  {'people': User.objects.\
                   filter(is_active=True, groups__name="Rep")
                   })


def view_profile(request, display_name):
    user = get_object_or_404(User, userprofile__display_name = display_name)
    return render(request, 'profiles_view.html', {'pageuser': user})


@permission_check(permissions=['profiles.create_user'])
def invite(request):
    if request.POST:
        form = forms.InviteUserForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                user = User.objects.create_user(username=username_algo(email),
                                                email=email)
                user.userprofile.added_by = request.user
                user.userprofile.save()

            except django.db.IntegrityError:
                messages.error(request, 'User already exists')

            else:
                messages.success(request, 'User was invited')
                return redirect('profiles_invite')

    else:
        form = forms.InviteUserForm()

    return render(request, "profiles_invite.html",
                  {'form': form}
                  )


@permission_check(permissions=['profiles.can_edit_profiles'])
def delete_user(request, display_name):
    user = get_object_or_404(User, userprofile__display_name=display_name)

    if request.POST:
        user.delete()
        messages.success(request, 'User was deleted')

    return redirect('main')


@permission_check()
def view_my_profile(request):
    return view_profile(request,
                        display_name=request.user.userprofile.display_name)


@anonymous_csrf
def plainlogin(request, template_name):
    return django_login(request, template_name=template_name)


