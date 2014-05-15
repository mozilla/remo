from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.forms.models import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from django_statsd.clients import statsd

import forms

from remo.base.decorators import permission_check
from remo.base.utils import get_or_create_instance
from remo.voting.helpers import user_has_poll_permissions
from remo.voting.models import Poll, PollComment, RadioPoll, RangePoll, Vote


@permission_check()
def list_votings(request):
    """List votings view."""
    user = request.user
    polls = Poll.objects.all()
    if not user.groups.filter(name='Admin').exists():
        polls = Poll.objects.filter(valid_groups__in=user.groups.all())

    past_polls_query = polls.filter(end__lt=now())
    current_polls = polls.filter(start__lt=now(), end__gt=now())
    future_polls = polls.filter(start__gt=now())

    past_polls_paginator = Paginator(past_polls_query, settings.ITEMS_PER_PAGE)
    past_polls_page = request.GET.get('page', 1)

    try:
        past_polls = past_polls_paginator.page(past_polls_page)
    except PageNotAnInteger:
        past_polls = past_polls_paginator.page(1)
    except EmptyPage:
        past_polls = past_polls_paginator.page(past_polls_paginator.num_pages)

    return render(request, 'list_votings.html',
                  {'user': user,
                   'past_polls': past_polls,
                   'current_polls': current_polls,
                   'future_polls': future_polls})


@permission_check(permissions=['voting.add_poll', 'voting.change_poll'])
def edit_voting(request, slug=None):
    """Create/Edit voting view."""
    poll, created = get_or_create_instance(Poll, slug=slug)

    can_delete_voting = False
    extra_range_polls = 0
    extra_radio_polls = 0
    current_voting_edit = False
    range_poll_formset = None
    radio_poll_formset = None

    if created:
        poll.created_by = request.user
        extra_range_polls = 1
        extra_radio_polls = 1
    else:
        if not poll.range_polls.exists():
            extra_range_polls = 1
        if not poll.radio_polls.exists():
            extra_radio_polls = 1
        can_delete_voting = True

        if poll.start < now() and poll.end > now():
            current_voting_edit = True
        if not user_has_poll_permissions(request.user, poll):
            messages.error(request, 'Permission denied.')
            return redirect('voting_list_votings')

    nominee_list = User.objects.filter(
        groups__name='Rep', userprofile__registration_complete=True)
    if current_voting_edit:
        poll_form = forms.PollEditForm(request.POST or None, instance=poll)
    else:
        RangePollFormset = (inlineformset_factory(Poll, RangePoll,
                            formset=forms.BaseRangePollInlineFormSet,
                            extra=extra_range_polls, can_delete=True))
        RadioPollFormset = (inlineformset_factory(Poll, RadioPoll,
                            formset=forms.BaseRadioPollInlineFormSet,
                            extra=extra_radio_polls, can_delete=True))

        range_poll_formset = RangePollFormset(request.POST or None,
                                              instance=poll,
                                              user_list=nominee_list)
        radio_poll_formset = RadioPollFormset(request.POST or None,
                                              instance=poll)
        poll_form = forms.PollAddForm(request.POST or None, instance=poll,
                                      radio_poll_formset=radio_poll_formset,
                                      range_poll_formset=range_poll_formset)

    if poll_form.is_valid():
        poll_form.save()

        if created:
            messages.success(request, 'Voting successfully created.')
            statsd.incr('voting.create_voting')
        else:
            messages.success(request, 'Voting successfully edited.')
            statsd.incr('voting.edit_voting')

        if not current_voting_edit:
            statsd.incr('voting.create_range_poll',
                        poll_form.radio_poll_formset.total_form_count())
            statsd.incr('voting.create_radio_poll',
                        poll_form.range_poll_formset.total_form_count())

        return redirect('voting_edit_voting', slug=poll.slug)

    return render(request, 'edit_voting.html',
                  {'creating': created,
                   'poll': poll,
                   'poll_form': poll_form,
                   'range_poll_formset': range_poll_formset,
                   'radio_poll_formset': radio_poll_formset,
                   'can_delete_voting': can_delete_voting,
                   'current_voting_edit': current_voting_edit,
                   'nominee_list': nominee_list})


@permission_check()
def view_voting(request, slug):
    """View voting and cast a vote view."""
    user = request.user
    poll = get_object_or_404(Poll, slug=slug)
    # If the user does not belong to a valid poll group
    if not user_has_poll_permissions(user, poll):
        messages.error(request, ('You do not have the permissions to '
                                 'vote on this voting.'))
        return redirect('voting_list_votings')

    range_poll_choice_forms = {}
    radio_poll_choice_forms = {}

    data = {'poll': poll}

    # if the voting period has ended, display the results
    if now() > poll.end:
        return render(request, 'view_voting.html', data)
    if now() < poll.start:
        # Admin can edit future votings
        if user.groups.filter(name='Admin').exists():
            return redirect('voting_edit_voting', slug=poll.slug)
        else:
            messages.warning(request, ('This vote has not yet begun. '
                                       'You can cast your vote on %s UTC.' %
                                       poll.start.strftime('%Y %B %d, %H:%M')))
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
        range_poll_choice_forms[item] = forms.RangePollChoiceVoteForm(
            data=request.POST or None, choices=item.choices.all())

    for item in poll.radio_polls.all():
        radio_poll_choice_forms[item] = forms.RadioPollChoiceVoteForm(
            data=request.POST or None, radio_poll=item)

    poll_comment = PollComment(poll=poll, user=request.user)
    poll_comment_form = forms.PollCommentForm(data=request.POST or None,
                                              instance=poll_comment)

    if request.method == 'POST':
        forms_valid = True
        # validate all forms
        for item in (range_poll_choice_forms.values()
                     + radio_poll_choice_forms.values()):
            if not item.is_valid():
                forms_valid = False
                break
        if poll.automated_poll and not poll_comment_form.is_valid():
            forms_valid = False

        if forms_valid:
            for range_poll_form in range_poll_choice_forms.values():
                range_poll_form.save()
            for radio_poll_form in radio_poll_choice_forms.values():
                radio_poll_form.save()
            if poll.automated_poll:
                poll_comment_form.save()
                statsd.incr('voting.create_automated_poll_comment')
            Vote.objects.create(user=user, poll=poll)
            messages.success(request, ('Your vote has been '
                                       'successfully registered.'))
            statsd.incr('voting.vote_voting')
            return redirect('voting_list_votings')

    data['range_poll_choice_forms'] = range_poll_choice_forms
    data['radio_poll_choice_forms'] = radio_poll_choice_forms
    data['poll_comment_form'] = poll_comment_form

    return render(request, 'vote_voting.html', data)


@permission_check(permissions=['voting.delete_poll'])
def delete_voting(request, slug):
    """Delete voting view."""
    if request.method == 'POST':
        voting = get_object_or_404(Poll, slug=slug)
        voting.delete()
        messages.success(request, 'Voting successfully deleted.')
        statsd.incr('voting.delete_voting')
    return redirect('voting_list_votings')
