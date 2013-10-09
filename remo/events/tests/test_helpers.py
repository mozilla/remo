from django.conf import settings
from django.core.urlresolvers import reverse

from nose.tools import eq_
from test_utils import TestCase

from ..models import Event
from ..helpers import *


class HelpersTest(TestCase):
    """Tests related to Events' Helpers."""
    fixtures = ['demo_users.json', 'demo_events.json']

    def test_is_multiday(self):
        """Test is_multiday filter."""
        e = Event.objects.get(slug='multi-event')
        eq_(is_multiday(e.local_start, e.local_end), True,
            'Multiday event validates to False')

        e = Event.objects.get(slug='test-event')
        eq_(is_multiday(e.local_start, e.local_end), False,
            'Single day event validates to True')

    def test_attendance_list_sorting(self):
        """Test sorting of event attendance list."""
        e = Event.objects.get(slug='test-event')

        sorted_list = get_sorted_attendance_list(e)
        eq_(sorted_list[0], e.owner, 'Owner is not first.')

        copy_list = sorted_list[1:]
        sorted(copy_list, key=lambda x: '%s %s' % (x.last_name, x.first_name))

        eq_(copy_list, sorted_list[1:],
            'List is not properly sorted.')

    def test_contribute_link(self):
        """Test /contribute link generation."""
        e = Event.objects.get(slug='test-event')
        url = (settings.CONTRIBUTE_URL %
               {'callbackurl': (settings.SITE_URL +
                                reverse('events_count_converted_visitors',
                                        kwargs={'slug': e.slug}))})
        eq_(get_contribute_link(e), url)

    def test_get_event_search_link(self):
        """Test event search link generation."""
        search = 'SearchTerm'
        url = reverse('events_list_events')
        eq_(get_event_search_link(search), urlparams(url, '/search/searchterm/'))
