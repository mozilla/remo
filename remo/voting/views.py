from datetime import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from remo.base.decorators import permission_check
from remo.base.utils import get_or_create_instance
from remo.voting.models import Poll

import forms


@permission_check()
def list_votings(request):
    """List votings view."""
    user = request.user
    now = datetime.now()
    polls = Poll.objects.all()
    if not user.groups.filter(name='Admin').exists():
        polls = Poll.objects.filter(valid_groups__in=user.groups.all())

    past_polls = polls.filter(end__lt=now)
    current_polls = polls.filter(start__lt=now, end__gt=now)
    future_polls = polls.filter(start__gt=now)

    return render(request, 'list_votings.html',
                  {'user': user,
                   'past_polls': past_polls,
                   'current_polls': current_polls,
                   'future_polls': future_polls})


@permission_check(group='Admin')
def edit_voting(request, slug=None):
    """Create/Edit voting view."""
    poll, created = get_or_create_instance(Poll, slug=slug)
    poll_form = forms.PollForm(request.POST or None, instance=poll)
    poll_range_formset = forms.PollRangeFormset(request.POST or None,
                                                instance=poll)
    poll_radio_formset = forms.PollRadioFormset(request.POST or None,
                                                instance=poll)
    can_delete_voting = False

    if created:
        poll.created_by = request.user
    else:
        can_delete_voting = True

    if (poll_form.is_valid() and poll_range_formset.is_valid()
            and poll_radio_formset.is_valid()):
        poll_form.save()
        poll_range_formset.save_all()
        poll_radio_formset.save_all()

        if created:
            messages.success(request, 'Voting successfully created.')
        else:
            messages.success(request, 'Voting successfully edited.')

        return redirect('voting_list_votings')

    return render(request, 'edit_voting.html',
                  {'creating': created,
                   'poll': poll,
                   'poll_form': poll_form,
                   'poll_range_formset': poll_range_formset,
                   'poll_radio_formset': poll_radio_formset,
                   'can_delete_voting': can_delete_voting})


@permission_check()
def view_voting(request, slug):
    """View voting view."""
    voting = get_object_or_404(Poll, slug=slug)
    return render(request, 'view_voting.html', {'voting': voting})
