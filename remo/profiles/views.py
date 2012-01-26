from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.views import login as django_login
from session_csrf import anonymous_csrf

@login_required
def edit(request, display_name=None):
    return HttpResponse("edit profile")


def list_profiles(request):
    return HttpResponse("list profiles")


def view_profile(request, display_name):
    return HttpResponse("view_profile")


def invite(request):
    return HttpResponse("invite")


@login_required
def view_my_profile(request):
    return view_profile(request,
                        display_name=request.user.userprofile.display_name)

@anonymous_csrf
def plainlogin(request, template_name):
    return django_login(request, template_name=template_name)
