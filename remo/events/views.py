import pytz
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.csrf import csrf_exempt

from funfactory.helpers import urlparams

from remo.base.decorators import permission_check
from remo.base.forms import EmailUsersForm
from remo.base.utils import get_or_create_instance

import forms
from models import Attendance, Event, EventComment


@never_cache
def redirect_list_events(request):
    events_url = reverse('events_list_events')
    extra_path = '/' + request.path_info[len(events_url):]
    return redirect(urlparams(events_url, hash=extra_path), permanent=True)


@cache_control(private=True)
def list_events(request):
    """List events view."""
    events = Event.objects.all()
    return render(request, 'list_events.html', {'events': events})


@never_cache
@permission_check(permissions=['events.can_subscribe_to_events'])
def manage_subscription(request, slug, subscribe=True):
    """Manage user's event subscription.

    When /subscribe/ == True then subscribe user to event if not
    already subscribed, else unsubscribe user.

    """
    event = get_object_or_404(Event, slug=slug)

    if request.method == 'POST':
        attendance, created = get_or_create_instance(Attendance,
                                                     user=get_user(request),
                                                     event=event)

        if subscribe:
            if not created:
                messages.warning(request, ('You are already subscribed to '
                                           'this event.'))
            else:
                attendance.save()
                messages.success(request, ('You have subscribed to '
                                           'this event.'))

        else:
            if created:
                messages.warning(request, ('You are not subscribed '
                                           'to this event.'))

            elif request.user == event.owner:
                messages.error(request, ('Event owner cannot unsubscribe '
                                         'from event.'))

            else:
                attendance.delete()
                messages.success(request, ('You have unsubscribed '
                                           'from this event.'))

    return redirect('events_view_event', slug=event.slug)


@cache_control(private=True)
def view_event(request, slug):
    """View event view."""
    event = get_object_or_404(Event, slug=slug)
    attendees = event.attendees.all()
    email_att_form = EmailUsersForm(attendees)

    if request.method == 'POST':
        if not request.user.is_authenticated():
            messages.error(request, 'Permission Denied')
            return redirect('main')

        event_comment = EventComment(event=event, user=request.user)
        event_comment_form = forms.EventCommentForm(request.POST,
                                                    instance=event_comment)
        if event_comment_form.is_valid():
            event_comment_form.save()
            messages.success(request, 'Comment saved')

            # provide new clean form
            event_comment_form = forms.EventCommentForm()
    else:
        event_comment_form = forms.EventCommentForm()

    event_url = reverse('events_view_event', kwargs={'slug': slug})

    return render(request, 'view_event.html',
                  {'event': event, 'email_attendees_form': email_att_form,
                   'comments': event.eventcomment_set.all(),
                   'event_comment_form': event_comment_form,
                   'event_comment_form_url': event_url})


@permission_check(permissions=['events.can_delete_event_comments'],
                  filter_field='pk', owner_field='user',
                  model=EventComment)
def delete_event_comment(request, slug, pk):
    if request.method == 'POST':
        if pk:
            event_comment = get_object_or_404(EventComment, pk=pk)
            event_comment.delete()
            messages.success(request, 'Comment successfully deleted.')

    event_url = reverse('events_view_event', kwargs={'slug': slug})

    return redirect(event_url)


@never_cache
@permission_check(permissions=['events.can_edit_events'])
def edit_event(request, slug=None):
    """Edit event view."""
    event, created = get_or_create_instance(Event, slug=slug)
    if created:
        event.owner = request.user
    else:
        # This is for backwards compatibility for all the events
        # that were set before the change in the minutes section
        # of the drop down widget to multiples of 5.
        # Start time: Floor rounding
        # End time: Ceilling rounding
        event.start -= timedelta(minutes=event.start.minute % 5)
        if (event.end.minute % 5) != 0:
            event.end += timedelta(minutes=(5 - (event.end.minute % 5)))

    if request.user.groups.filter(name='Admin').count():
        event_form = forms.EventForm(request.POST or None,
                                     editable_owner=True, instance=event)
    else:
        event_form = forms.EventForm(request.POST or None,
                                     editable_owner=False, instance=event)
    metrics_formset = forms.EventMetricsFormset(request.POST or None,
                                                instance=event)

    if (event_form.is_valid() and metrics_formset.is_valid()):
        event_form.save()
        metrics_formset.save()

        if created:
            messages.success(request, 'Event successfully created.')
        else:
            messages.success(request, 'Event successfully updated.')

        return redirect('events_view_event', slug=event_form.instance.slug)

    can_delete_event = False
    if (not created and
        (event.owner == request.user or
         request.user.has_perm('events.can_delete_events'))):
        can_delete_event = True

    return render(request, 'edit_event.html',
                  {'creating': created,
                   'event': event,
                   'event_form': event_form,
                   'metrics_formset': metrics_formset,
                   'can_delete_event': can_delete_event})


@never_cache
@permission_check(permissions=['events.can_delete_events'],
                  owner_field='owner', model=Event,
                  filter_field='slug')
def delete_event(request, slug):
    """Delete event view."""
    if request.method == 'POST':
        event = get_object_or_404(Event, slug=slug)
        event.delete()
        messages.success(request, 'Event successfully deleted.')

    return redirect('events_list_events')


@never_cache
@csrf_exempt
def count_converted_visitors(request, slug):
    """Increase event subscribers."""
    event = get_object_or_404(Event, slug=slug)

    if request.method == 'POST':
        event.converted_visitors += 1
        event.save()
        return HttpResponse('OK')

    return redirect('events_view_event', slug=event.slug)


@never_cache
def export_single_event_to_ical(request, slug):
    """ICal export of single event."""
    event = get_object_or_404(Event, slug=slug)
    my_uuid = uuid.uuid4()
    date_now = timezone.make_aware(datetime.now(), pytz.UTC)
    ical = render(request, 'ical_template.ics', {'event': event,
                                                 'uuid': my_uuid,
                                                 'date_now': date_now,
                                                 'host': settings.SITE_URL})
    response = HttpResponse(ical, mimetype='text/calendar')
    ical_filename = event.slug + '.ics'
    response['Filename'] = ical_filename
    response['Content-Disposition'] = ('attachment; filename="%s"' %
                                       (ical_filename))
    return response


@login_required
def email_attendees(request, slug):
    """Send email to event attendees."""
    event = get_object_or_404(Event, slug=slug)
    attendees = event.attendees.all()

    if request.method == 'POST':
        email_form = EmailUsersForm(attendees, request.POST)
        if email_form.is_valid():
            email_form.send_mail(request)
        else:
            messages.error(request, 'Email not sent. Invalid data.')
    return redirect('events_view_event', slug=slug)
