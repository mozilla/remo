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
from remo.profiles.models import UserProfile
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

        if poll.is_current_voting:
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
                  {'created': created,
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
    user_voted = False
    comment_form = forms.PollCommentForm()

    data = {'poll': poll,
            'comment_form': comment_form}

    # if the voting period has ended, display the results
    if poll.is_past_voting:
        return render(request, 'view_voting.html', data)

    # avoid multiple votes from the same user
    if Vote.objects.filter(poll=poll, user=user).exists():
        if not poll.comments_allowed:
            messages.warning(request, ('You have already cast your vote for '
                                       'this voting. Come back to see the '
                                       'results on %s UTC.'
                                       % poll.end.strftime('%Y %B %d, %H:%M')))
            return redirect('voting_list_votings')
        # If the poll allows comments, display them along with an info msg
        user_voted = True
        data['user_voted'] = user_voted

        msg = "You have already cast your vote for this voting."
        messages.info(request, msg)

    # pack the forms for rendering
    for item in poll.range_polls.all():
        range_poll_choice_forms[item] = forms.RangePollChoiceVoteForm(
            data=request.POST or None, choices=item.choices.all())

    for item in poll.radio_polls.all():
        radio_poll_choice_forms[item] = forms.RadioPollChoiceVoteForm(
            data=request.POST or None, radio_poll=item)

    if request.method == 'POST':
        # Process comment form
        if 'comment' in request.POST and poll.comments_allowed:
            comment_form = forms.PollCommentForm(request.POST)
            if comment_form.is_valid():
                obj = comment_form.save(commit=False)
                obj.user = request.user
                obj.poll = poll
                obj.save()
                messages.success(request, 'Comment saved successfully.')
                data['comment_form'] = forms.PollCommentForm()
            return redirect(poll.get_absolute_url())
        else:
            # Process poll form
            forms_valid = True
            # validate all forms
            for item in (range_poll_choice_forms.values()
                         + radio_poll_choice_forms.values()):
                if not item.is_valid():
                    forms_valid = False
                    break

            if forms_valid and poll.is_current_voting:
                for range_poll_form in range_poll_choice_forms.values():
                    range_poll_form.save()
                for radio_poll_form in radio_poll_choice_forms.values():
                    radio_poll_form.save()

                Vote.objects.create(user=user, poll=poll)
                messages.success(request, ('Your vote has been '
                                           'successfully registered.'))
                statsd.incr('voting.vote_voting')
                return redirect('voting_list_votings')

    data['range_poll_choice_forms'] = range_poll_choice_forms
    data['radio_poll_choice_forms'] = radio_poll_choice_forms

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


@permission_check(permissions=['voting.delete_pollcomment'],
                  filter_field='display_name', owner_field='user',
                  model=UserProfile)
def delete_poll_comment(request, slug, comment_id):
    poll = get_object_or_404(Poll, slug=slug)
    if comment_id and request.method == 'POST':
        poll_comment = get_object_or_404(PollComment, pk=comment_id)
        poll_comment.delete()
        messages.success(request, 'Comment successfully deleted.')
    return redirect(poll.get_absolute_url())
