import pytz
from datetime import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone

from funfactory.helpers import urlparams
from jingo import register


@register.filter
def get_event_converted_visitor_callback_url(obj):
    """Return event converted visitor callback url."""
    return settings.SITE_URL + reverse('events_count_converted_visitors',
                                       kwargs={'slug': obj.slug})


@register.function
def get_link_to_osm(lat, lon, zoom=15):
    """Return link to OSM centered in lat, lon."""
    return ('http://openstreetmap.org/?mlat=%(lat)s&mlon=%(lon)s'
            '&zoom=%(zoom)s' % {'lat': lat, 'lon': lon, 'zoom': zoom})


@register.function
def get_link_to_gmaps(lat, lon, label='', zoom=15):
    """Return link to gmaps map centered in lat, lon."""
    return ('https://maps.google.com/maps?ll=%(lat)s,%(lon)s'
            '&q=%(label)s@%(lat)s,%(lon)s&zoom=%(zoom)s' % {'lat': lat,
                                                            'lon': lon,
                                                            'label': label,
                                                            'zoom': zoom})


@register.function
def get_attendee_role_event(attendee, event):
    """Return attendee's role in event."""
    if attendee == event.owner:
        if event.mozilla_event:
            return 'Organizer'
        else:
            return 'Mozilla\'s presence organizer'
    elif attendee.groups.filter(name='Mozillians').exists():
        return 'Mozillian attendee'

    return 'Rep attendee'


@register.function
def is_multiday(start, end):
    """Return True if event is multiday.

    Fancy way to compare 'year', 'month' and 'day' attributes of two objects
    and return True only if all pairs match.
    """

    return not reduce(lambda x, y: (x == y) is True,
                      map(lambda x: (getattr(end, x) == getattr(start, x)),
                          ['year', 'month', 'day']))


@register.function
def get_sorted_attendance_list(event):
    """Sorts attendance list by last_name, first_name and always
    places owner on the top.

    """

    attendees = list(event.attendees.all().order_by('last_name', 'first_name'))
    attendees.remove(event.owner)
    attendees.insert(0, event.owner)
    return attendees


@register.function
def get_contribute_link(event):
    """Returns custom link to m.o/contribute."""

    return (settings.CONTRIBUTE_URL %
            {'callbackurl': (settings.SITE_URL +
                             reverse('events_count_converted_visitors',
                                     kwargs={'slug': event.slug}))})


@register.function
def is_past_event(event):
    """Checks if an event has already taken place."""

    now = timezone.make_aware(datetime.now(), pytz.UTC)
    return now > event.end


@register.filter
def get_event_comment_delete_url(obj):
    """Return the delete url of an event comment."""

    return reverse('events_delete_event_comment',
                   kwargs={'slug': obj.event.slug,
                           'pk': obj.id})


@register.function
def get_event_category_link(category):
    """Returns events list page of given category."""

    url = reverse('events_list_events')
    return urlparams(url, '/category/%s/' % category.lower())


@register.function
def get_event_search_link(search):
    """Returns events list page with the given search term."""

    url = reverse('events_list_events')
    return urlparams(url, '/search/%s/' % search.lower())


@register.function
def get_event_link(event):
    """Returns events url."""

    return (settings.SITE_URL +
            reverse('events_view_event', kwargs={'slug': event.slug}))
