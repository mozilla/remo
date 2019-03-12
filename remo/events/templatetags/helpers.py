from django.conf import settings
from django.core.urlresolvers import reverse

from django_jinja import library

from remo.base.templatetags.helpers import urlparams


@library.global_function
def get_link_to_osm(lat, lon, zoom=15):
    """Return link to OSM centered in lat, lon."""
    return ('http://openstreetmap.org/?mlat=%(lat)s&mlon=%(lon)s'
            '&zoom=%(zoom)s' % {'lat': lat, 'lon': lon, 'zoom': zoom})


@library.global_function
def get_link_to_gmaps(lat, lon, label='', zoom=15):
    """Return link to gmaps map centered in lat, lon."""
    return ('https://maps.google.com/maps?ll=%(lat)s,%(lon)s'
            '&q=%(label)s@%(lat)s,%(lon)s&zoom=%(zoom)s' % {'lat': lat,
                                                            'lon': lon,
                                                            'label': label,
                                                            'zoom': zoom})


@library.global_function
def get_attendee_role_event(attendee, event):
    """Return attendee's role in event."""
    if attendee == event.owner:
        if event.mozilla_event:
            return 'Organizer'
        else:
            return 'Mozilla\'s presence organizer'
    elif attendee.groups.filter(name='Mozillians').exists():
        return 'Mozillian attendee'
    elif attendee.groups.filter(name='Alumni').exists():
        return 'Alumni attendee'
    return 'Rep attendee'


@library.global_function
def is_multiday(start, end):
    """Return True if event is multiday.

    Fancy way to compare 'year', 'month' and 'day' attributes of two objects
    and return True only if all pairs match.
    """

    return not reduce(lambda x, y: (x is y is True),
                      map(lambda x: (getattr(end, x) == getattr(start, x)),
                          ['year', 'month', 'day']))


@library.global_function
def get_sorted_attendance_list(event):
    """Sorts attendance list by last_name, first_name and always
    places owner on the top.

    """

    query = event.attendees.exclude(groups__name='Mozillians',
                                    userprofile__mozillian_username='')
    attendees = list(query.order_by('last_name', 'first_name'))
    if event.owner in attendees:
        attendees.remove(event.owner)
        attendees.insert(0, event.owner)
    return attendees


@library.filter
def get_total_attendees(event):
    """Return the total number of people attending an event."""
    return event.attendees.all().count()


@library.filter
def get_event_comment_delete_url(obj):
    """Return the delete url of an event comment."""

    return reverse('events_delete_event_comment',
                   kwargs={'slug': obj.event.slug,
                           'pk': obj.id})


@library.global_function
def get_event_filtered_url(category=None, initiative=None):
    """Returns events list page of given category or initiative."""

    url = reverse('events_list_events')
    if category:
        return urlparams(url, '/category/%s/' % category.lower())
    elif initiative:
        return urlparams(url, '/initiative/%s/' % initiative.lower())
    else:
        return url


@library.global_function
def get_event_search_link(search):
    """Returns events list page with the given search term."""

    url = reverse('events_list_events')
    return urlparams(url, '/search/%s/' % search.lower())


@library.global_function
def get_event_link(event):
    """Returns events url."""

    return (settings.SITE_URL
            + reverse('events_view_event', kwargs={'slug': event.slug}))
