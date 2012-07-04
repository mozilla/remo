from django.contrib import messages
from django.contrib.auth import get_user
from django.shortcuts import get_object_or_404, redirect, render

from remo.base.decorators import permission_check
from remo.base.utils import get_or_create_instance

import forms
from models import Attendance, Event


def list_events(request):
    """List events view."""
    events = Event.objects.all()

    return render(request, 'list_events.html', {'events': events})


@permission_check(permissions=['events.can_subscribe_to_events'])
def manage_subscription(request, slug, subscribe=True):
    """Manage user's event subscription.

    When /subscribe/ == True then subscribe user to event if not
    already subscribed, else unsubscribe user.

    """
    event = get_object_or_404(Event, slug=slug)
    attendace, created = get_or_create_instance(Attendance,
                                                user=get_user(request),
                                                event=event)

    if subscribe:
        if not created:
            messages.warning(request, ('You are already subscribed to '
                                      'this event.'))
            return redirect('events_view_event', slug=event.slug)

        attendace.save()
        messages.success(request, ('You have subscribed to this event.'))
        return redirect('events_view_event', slug=event.slug)

    else:
        if created:
            messages.warning(request, 'You are not subscribed to this event.')
            return redirect('events_view_event', slug=event.slug)

        attendace.delete()
        messages.success(request, ('You have unsubscribed from this event.'))
        return redirect('events_view_event', slug=event.slug)


def view_event(request, slug):
    """View event view."""
    event = get_object_or_404(Event, slug=slug)

    return render(request, 'view_event.html', {'event': event})


@permission_check(permissions=['events.can_edit_events'])
def edit_event(request, slug=None):
    """Edit event view."""
    event, created = get_or_create_instance(Event, slug=slug)
    event_form = forms.EventForm(request.POST or None, instance=event)

    if event_form.is_valid():
        event_form.save()

        if created:
            messages.success(request, 'Event successfully created.')
        else:
            messages.success(request, 'Event successfully updated.')

        return redirect('events_view_event', slug=event_form.instance.slug)

    return render(request, 'edit_event.html', {'event_form': event_form})


@permission_check(permissions=['events.can_delete_events'],
                  owner_field='owner', model=Event,
                  filter_field='slug')
def delete_event(request, slug):
    """Delete event view."""
    event = get_object_or_404(Event, slug=slug)
    event.delete()

    messages.success(request, 'Event successfully deleted.')
    return redirect('events_list_events')
