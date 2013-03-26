import pytz
from datetime import datetime

from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.forms.models import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import make_aware

from remo.base.decorators import permission_check
from remo.base.utils import get_or_create_instance
from remo.voting.models import Poll, RadioPoll, RangePoll, Vote

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

    can_delete_voting = False
    extra = 0
    current_voting_edit = False
    range_poll_formset = None
    radio_poll_formset = None
    if created:
        poll.created_by = request.user
        extra = 1
    else:
        if (RangePoll.objects.filter(poll=poll).count() or
                RadioPoll.objects.filter(poll=poll).count()) == 0:
            extra = 1
        can_delete_voting = True
        date_now = make_aware(datetime.now(),
                              pytz.timezone(settings.TIME_ZONE))
        if poll.start < date_now and poll.end > date_now:
            current_voting_edit = True

    if current_voting_edit:
        poll_form = forms.PollEditForm(request.POST or None, instance=poll)
    else:
        poll_form = forms.PollAddForm(request.POST or None, instance=poll)

        RangePollFormset = (inlineformset_factory(Poll, RangePoll,
                            formset=forms.BaseRangePollInlineFormSet,
                            extra=extra, can_delete=True))
        RadioPollFormset = (inlineformset_factory(Poll, RadioPoll,
                            formset=forms.BaseRadioPollInlineFormSet,
                            extra=extra, can_delete=True))

        range_poll_formset = RangePollFormset(request.POST or None,
                                              instance=poll)
        radio_poll_formset = RadioPollFormset(request.POST or None,
                                              instance=poll)

    if poll_form.is_valid():
        if current_voting_edit:
            poll_form.save()
        elif range_poll_formset.is_valid() and radio_poll_formset.is_valid():
            poll_form.save()
            range_poll_formset.save_all()
            radio_poll_formset.save_all()

        if created:
            messages.success(request, 'Voting successfully created.')
        else:
            messages.success(request, 'Voting successfully edited.')

        return redirect('voting_edit_voting', slug=poll.slug)

    return render(request, 'edit_voting.html',
                  {'creating': created,
                   'poll': poll,
                   'poll_form': poll_form,
                   'range_poll_formset': range_poll_formset,
                   'radio_poll_formset': radio_poll_formset,
                   'can_delete_voting': can_delete_voting,
                   'current_voting_edit': current_voting_edit})


@permission_check()
def view_voting(request, slug):
    """View voting and cast a vote view."""
    user = request.user
    now = make_aware(datetime.now(), pytz.timezone(settings.TIME_ZONE))
    poll = get_object_or_404(Poll, slug=slug)
    # If the user does not belong to a valid poll group
    if not (user.groups.filter(Q(id=poll.valid_groups.id) |
                               Q(name='Admin')).exists()):
        messages.error(request, ('You do not have the permissions to '
                                 'vote on this voting.'))
        return redirect('voting_list_votings')

    range_poll_choice_forms = {}
    radio_poll_choice_forms = {}

    data = {'poll': poll}

    # if the voting period has ended, display the results
    if now > poll.end:
        return render(request, 'view_voting.html', data)
    if now < poll.start:
        # Admin can edit future votings
        if user.groups.filter(name='Admin').exists():
            return redirect('voting_edit_voting', slug=poll.slug)
        else:
            messages.warning(request, ('This vote has not yet begun. '
                                       'You can cast your vote on %s PDT.' %
                                       poll.start.strftime('%Y %B %d, %H:%M')))
            return redirect('voting_list_votings')

    # avoid multiple votes from the same user
    if Vote.objects.filter(poll=poll, user=user).exists():
        messages.warning(request, ('You have already cast your vote for this '
                                   'voting. Come back to see the results on '
                                   '%s PDT.'
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


@permission_check(group='Admin')
def delete_voting(request, slug):
    """Delete voting view."""
    if request.method == 'POST':
        voting = get_object_or_404(Poll, slug=slug)
        voting.delete()
        messages.success(request, 'Voting successfully deleted.')
    return redirect('voting_list_votings')
