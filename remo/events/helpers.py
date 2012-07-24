from django.conf import settings
from django.core.urlresolvers import reverse
from jingo import register


@register.filter
def get_event_converted_visitor_callback_url(obj):
    """Return event converted visitor callback url."""
    return settings.SITE_URL + reverse('events_count_converted_visitors',
                                       kwargs={'slug': obj.slug})


@register.function
def get_link_to_cloudmade(lat, lon, zoom=15):
    """Return link to cloudmade map centered in lat, lon."""
    return ('http://maps.cloudmade.com/?lat=%(lat)s&lng=%(lon)s'
            '&zoom=%(zoom)s&styleId=997'
            '&marker=%(lon)s,%(lat)s' % {'lat': lat,
                                         'lon': lon,
                                         'zoom': zoom})


@register.function
def get_link_to_gmaps(lat, lon, label='', zoom=15):
    """Return link to cloudmade map centered in lat, lon."""
    return ('https://maps.google.com/maps?ll=%(lat)s,%(lon)s'
            '&q=%(label)s@%(lat)s,%(lon)s&z=%(zoom)s' % {'lat': lat,
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

    return 'Rep attendee'


@register.filter
def is_multiday(event):
    """Return True is event is multiday.

    Fancy way to compare 'year', 'month' and 'day' attributes of two objects
    and return True only if all pairs match.
    """

    return not reduce(lambda x, y: x == y == True,
                      map(lambda x: (getattr(event.end, x) ==
                                     getattr(event.start, x)),
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
