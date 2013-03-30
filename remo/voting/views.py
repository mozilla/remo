import pytz
from datetime import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from remo.base.decorators import permission_check
from remo.voting.models import Poll, Vote

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
    return render(request, 'edit_voting.html')


@permission_check()
def view_voting(request, slug):
    """View voting and cast a vote view."""
    user = request.user
    now = timezone.make_aware(datetime.now(), pytz.UTC)
    poll = get_object_or_404(Poll, slug=slug)
    range_poll_choice_forms = {}
    radio_poll_choice_forms = {}

    data = {'poll': poll}

    # if the voting period has ended, display the results
    if now > poll.end:
        return render(request, 'view_voting.html', data)
    if now < poll.start:
        messages.warning(request, ('This vote has not yet begun. '
                                   'You can cast your vote on %s UTC.'
                                   % poll.start.strftime('%Y %B %d, %H:%M')))
        return redirect('voting_list_votings')

    # avoid multiple votes from the same user
    if Vote.objects.filter(poll=poll, user=user).exists():
        messages.warning(request, ('You have already cast your vote for this '
                                   'voting. Come back to see the results on '
                                   '%s UTC.'
                                   % poll.end.strftime('%Y %B %d, %H:%M')))
        return redirect('voting_list_votings')

    # pack the forms for rendering
    for item in poll.range_polls.all():
        range_poll_choice_forms[item] = forms.RangePollChoiceForm(
            data=request.POST or None, choices=item.choices.all())

    for item in poll.radio_polls.all():
        radio_poll_choice_forms[item] = forms.RadioPollChoiceForm(
            data=request.POST or None, radio_poll=item)

    if request.method == 'POST':
        forms_valid = True
        # validate all forms
        for item in (range_poll_choice_forms.values()
                     + radio_poll_choice_forms.values()):
            if not item.is_valid():
                forms_valid = False
                break

        if forms_valid:
            for range_poll_form in range_poll_choice_forms.values():
                range_poll_form.save()
            for radio_poll_form in radio_poll_choice_forms.values():
                radio_poll_form.save()
            Vote.objects.create(user=user, poll=poll)
            messages.success(request, ('Your vote has been '
                                       'successfully registered.'))
            return redirect('voting_list_votings')

    data['range_poll_choice_forms'] = range_poll_choice_forms
    data['radio_poll_choice_forms'] = radio_poll_choice_forms

    return render(request, 'vote_voting.html', data)
