import datetime

from django.conf import settings
from django.core.urlresolvers import reverse

from nose.tools import eq_, ok_

from remo.base.templatetags.helpers import urlparams
from remo.base.tests import RemoTestCase
from remo.events.templatetags.helpers import (get_contribute_link, get_event_search_link,
                                              get_sorted_attendance_list, is_multiday)
from remo.events.tests import AttendanceFactory, EventFactory, START_DT
from remo.reports import ACTIVITY_EVENT_CREATE
from remo.reports.tests import ActivityFactory


class HelpersTest(RemoTestCase):
    """Tests related to Events' Helpers."""

    def setUp(self):
        ActivityFactory.create(name=ACTIVITY_EVENT_CREATE)
        self.single_day_end = START_DT + datetime.timedelta(hours=4)

    def test_is_multiday(self):
        """Test is_multiday filter."""
        e = EventFactory.create()
        ok_(is_multiday(e.start, e.end), 'Multiday event validates to False')

        e = EventFactory.create(start=START_DT, end=self.single_day_end)
        ok_(not is_multiday(e.start, e.end),
            'Single day event validates to True')

    def test_attendance_list_sorting(self):
        """Test sorting of event attendance list."""
        e = EventFactory.create(start=START_DT, end=self.single_day_end)
        AttendanceFactory.create_batch(2, event=e)

        sorted_list = get_sorted_attendance_list(e)
        eq_(sorted_list[0], e.owner, 'Owner is not first.')

        copy_list = sorted_list[1:]
        sorted(copy_list, key=lambda x: '%s %s' % (x.last_name, x.first_name))

        eq_(copy_list, sorted_list[1:],
            'List is not properly sorted.')

    def test_contribute_link(self):
        """Test /contribute link generation."""
        e = EventFactory.create(start=START_DT, end=self.single_day_end)
        url = (settings.CONTRIBUTE_URL %
               {'callbackurl': (settings.SITE_URL +
                                reverse('events_count_converted_visitors',
                                        kwargs={'slug': e.slug}))})
        eq_(get_contribute_link(e), url)

    def test_get_event_search_link(self):
        """Test event search link generation."""
        search = 'SearchTerm'
        url = reverse('events_list_events')
        eq_(get_event_search_link(search),
            urlparams(url, '/search/searchterm/'))
