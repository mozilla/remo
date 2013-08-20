from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_control, never_cache

from remo.base.decorators import permission_check

import forms
from models import FeaturedRep


@cache_control(private=True, max_age=60*10)
def list_featured(request):
    """List all Featured Reps."""
    return render(request, 'featuredrep_list.html',
                  {'featured': FeaturedRep.objects.all()})


@never_cache
@permission_check(permissions=['featuredrep.can_edit_featured'])
def edit_featured(request, feature_id=None):
    """Create or edit a Featured Rep.

    If feature_id == None then a new Featured Rep entry is created,
    otherwise the Featured Rep entry with id == feature_id is edited.

    """
    if feature_id:
        feature = get_object_or_404(FeaturedRep, pk=feature_id)
        post_to = reverse('featuredrep_edit_featured', args=[feature_id])
    else:
        feature = FeaturedRep(created_by=request.user)
        post_to = reverse('featuredrep_add_featured')

    form = forms.FeaturedRepForm(request.POST or None, instance=feature)

    if form.is_valid():
        form.save()

        if feature_id:
            messages.success(
                request, 'Featured rep article successfuly edited.')
        else:
            messages.success(request, 'New featured rep article created.')

        return redirect('featuredrep_list_featured')

    # List only user that belong in Rep group and have completed
    # registration.
    reps = User.objects.filter(userprofile__registration_complete=True,
                               groups__name='Rep')

    return render(request, 'featuredrep_alter.html',
                  {'form': form, 'post_to': post_to, 'reps': reps})


@permission_check(permissions=['featuredrep.can_delete_featured'])
def delete_featured(request, feature_id):
    """Delete a Featured Rep entry."""
    if request.method == 'POST':
        feature = get_object_or_404(FeaturedRep, pk=feature_id)
        feature.delete()
        messages.success(request, 'Featured rep article successfuly deleted')

    return redirect('featuredrep_list_featured')
