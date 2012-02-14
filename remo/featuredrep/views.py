# Create your views here. <-- you don't need this comment.
# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.urlresolvers import reverse

from session_csrf import anonymous_csrf

from remo.featuredrep.models import FeaturedRep
from remo.base.decorators import permission_check
# alphabetize your imports per section (section based on line breaks)

import forms
# two line breaks required
@permission_check(permissions=['profiles.can_edit_profiles'])
def list_featured(request):
    # Needs comment
    form = forms.FeaturedRepForm()

    return render(request,
                  'featuredrep_list.html',
                  { 'featured': FeaturedRep.objects.all() }
                  ) # bracket should be at the end of the curly brace above


@permission_check(permissions=['profiles.can_edit_profiles'])
def alter_featured(request, feature_id=None):
    # Needs comment
    if feature_id:
        feature = get_object_or_404(FeaturedRep, pk=feature_id)
        post_to = reverse('featuredrep_edit_featured', args=[feature_id])

    else:
        feature = FeaturedRep(created_by=request.user)
        post_to = reverse('featuredrep_add_featured')

    if request.method == 'POST':
        form = forms.FeaturedRepForm(request.POST, instance=feature)

        if form.is_valid():
            form.save()

            if feature_id:
                messages.success(request, 'New featured rep article created ☺')

            else:
                messages.success(request,
                                 'Featured rep article successfuly edited ☺')

            return redirect('featuredrep_list_featured')

    else:
        form = forms.FeaturedRepForm(instance=feature)

    return render(request, 'featuredrep_alter.html',
                  {'form':form,
                   'post_to': post_to,
                   'reps':User.objects.filter(
                       userprofile__registration_complete=True,
                       groups__name="Rep")
                   })


@permission_check(permissions=['profiles.can_edit_profiles'])
def delete_featured(request, feature_id):
    # Needs comment
    if request.method == 'POST':
        feature = get_object_or_404(FeaturedRep, pk=feature_id)
        feature.delete()
        messages.success(request, 'Featured rep article successfuly deleted')

    return redirect('featuredrep_list_featured')
# Extra line break here, should only be 1 line break
