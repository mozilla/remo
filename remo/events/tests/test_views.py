import datetime
from pytz import timezone

from django.core import management
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.client import Client
from django.utils.timezone import make_aware
from nose.tools import eq_
from test_utils import TestCase

from remo.events.models import Event, Metric


class ViewsTest(TestCase):
    """Tests related to Events Views."""
    fixtures = ['demo_users.json', 'demo_events.json']

    def setUp(self):
        self.data = {
            'name': u'Test edit event',
            'description': u'This is a description',
            'external_link': '',
            'venue': u'Hackerspace.GR',
            'lat': 38.01697,
            'lon': 23.7314,
            'city': u'Athens',
            'region': u'Attica',
            'country': u'Greece',
            'start_form_0_month': 01,
            'start_form_0_day': 25,
            'start_form_0_year': 2014,
            'start_form_1_hour': 04,
            'start_form_1_minute': 01,
            'end_form_0_month': 01,
            'end_form_0_day': 03,
            'end_form_0_year': 2018,
            'end_form_1_hour': 03,
            'end_form_1_minute': 00,
            'timezone': u'Europe/Athens',
            'owner_form': u'Koki Foci :koki',
            'mozilla_event': u'on',
            'estimated_attendance': u'10',
            'extra_content': u'This is extra content',
            'planning_pad_url': u'',
            'hashtag': u'#testevent',
            'swag_bug_form': u'',
            'budget_bug_form': u'',
            'metrics-0-title': u'First metric',
            'metrics-0-outcome': u'First outcome',
            'metrics-1-title': u'Second metric',
            'metrics-1-outcome': u'Second outcome',
            'metrics-2-title': u'Third metric',
            'metrics-2-outcome': u'Third outcome',
            'metrics-TOTAL_FORMS': 3,
            'metrics-INITIAL_FORMS': 0}

        self.pad_url = getattr(settings, 'ETHERPAD_URL', None)
        self.pad_prefix = getattr(settings, 'ETHERPAD_PREFIX', None)
        self.event_edit_url = reverse('events_edit_event',
                                      kwargs={'slug': 'test-event'})
        self.event_url = reverse('events_view_event',
                                 kwargs={'slug': 'test-event'})

    def test_view_events_list(self):
        """Get list events page."""
        c = Client()
        response = c.get(reverse('events_list_events'))
        self.assertTemplateUsed(response, 'list_events.html')

    def test_view_event_page(self):
        """Get view event page."""
        c = Client()
        response = c.get(reverse('events_view_event',
                                 kwargs={'slug': 'test-event'}))
        self.assertTemplateUsed(response, 'view_event.html')

    def test_subscribe_to_event(self):
        """Subscribe to event."""
        c = Client()

        # Anonymous user.
        response = c.post(reverse('events_subscribe_to_event',
                                  kwargs={'slug': 'test-event'}),
                          follow=True)
        self.assertTemplateUsed(response, 'main.html',
                                ('Anonymous user is not returned to '
                                 'main.html to login'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning', 'Anonymous user does not get a warning.')

        # Logged in user.
        c.login(username='rep3', password='passwd')
        response = c.post(reverse('events_subscribe_to_event',
                                  kwargs={'slug': 'test-event'}),
                          follow=True)
        self.assertTemplateUsed(response, 'view_event.html',
                                ('Rep user is not returned to '
                                 'event page after subscribing.'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')

        # Subscribed tries again.
        response = c.post(reverse('events_subscribe_to_event',
                                  kwargs={'slug': 'test-event'}),
                          follow=True)
        self.assertTemplateUsed(response, 'view_event.html',
                                ('Rep user is not returned to '
                                 'event page after subscribing.'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning', 'User does not get a warning message.')

    def test_unsubscribe_to_event(self):
        """Unsubscribe from event"""
        c = Client()

        # Anonymous user.
        response = c.post(reverse('events_unsubscribe_from_event',
                                  kwargs={'slug': 'test-event'}),
                          follow=True)
        self.assertTemplateUsed(response, 'main.html',
                                ('Anonymous user is not returned to '
                                 'main.html to login'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning', 'Anonymous user does not get a warning.')

        # Logged in user.
        c.login(username='mentor', password='passwd')
        response = c.post(reverse('events_unsubscribe_from_event',
                                  kwargs={'slug': 'test-event'}),
                          follow=True)
        self.assertTemplateUsed(response, 'view_event.html',
                                ('Rep user is not returned to '
                                 'event page after unsubscribing.'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success', 'User does not get a success message.')

        # Subscribed tries again.
        response = c.post(reverse('events_unsubscribe_from_event',
                                  kwargs={'slug': 'test-event'}),
                          follow=True)
        self.assertTemplateUsed(response, 'view_event.html',
                                ('Rep user is not returned to '
                                 'event page after unsubscribing.'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning', 'User does not get a warning message.')

    def test_delete_event(self):
        """Delete event."""
        c = Client()

        # Anonymous user.
        response = c.get(reverse('events_delete_event',
                                 kwargs={'slug': 'test-event'}),
                         follow=True)
        self.assertTemplateUsed(response, 'main.html',
                                ('Anonymous user is not returned to '
                                 'main.html to login'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning', 'Anonymous user does not get a warning.')

        # Rep (no permission).
        c.login(username='rep3', password='passwd')
        response = c.get(reverse('events_delete_event',
                                 kwargs={'slug': 'test-event'}),
                         follow=True)
        self.assertTemplateUsed(response, 'main.html',
                                ('Rep is not returned to main.html.'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error', 'Rep does not get an error.')

        # Mentor, Admin and Owner
        for user in ['mentor', 'admin', 'rep']:
            c.login(username=user, password='passwd')
            response = c.post(reverse('events_delete_event',
                                      kwargs={'slug': 'test-event'}),
                              follow=True)
            self.assertTemplateUsed(response, 'list_events.html',
                                    ('User %s not returned to '
                                     'main.html.' % user))
            for m in response.context['messages']:
                pass
            eq_(m.tags, u'success', ('User %s does not get an '
                                     'success message.' % user))

            # Reload events, since they get deleted.
            management.call_command('loaddata', 'demo_events')

    def test_converted_visitors(self):
        """Test converted visitors counter."""
        c = Client()
        c.post(reverse('events_count_converted_visitors',
                       kwargs={'slug': 'test-event'}))
        event = Event.objects.get(slug='test-event')
        eq_(event.converted_visitors, 2)

    def test_export_event_to_ical(self):
        """Test ical export."""
        c = Client()
        response = c.get(reverse('events_icalendar_event',
                                 kwargs={'slug': 'test-event'}))
        self.assertTemplateUsed(response, 'ical_template.ics')
        self.failUnless(response['Content-Type'].startswith('text/calendar'))

    def test_edit_event(self):
        """Edit event page"""
        c = Client()

        # Login as test-event owner
        c.login(username='rep', password='passwd')

        response = c.post(self.event_edit_url, self.data, follow=True)
        eq_(response.request['PATH_INFO'], self.event_url)

        # Ensure event data are saved
        event = Event.objects.get(name='Test edit event')

        # Test fields with the same name in POST data and models
        excluded = ['planning_pad_url', 'lat', 'lon', 'mozilla_event']
        for field in set(self.data).difference(set(excluded)):
            if getattr(event, field, None):
                eq_(str(getattr(event, field)), self.data[field])

        # Test excluded fields
        pad_url = self.pad_url + self.pad_prefix + event.slug
        mozilla_event = {'on': True, 'off': False}

        eq_(event.planning_pad_url, pad_url)
        eq_(event.lat, self.data['lat'])
        eq_(event.lon, self.data['lon'])
        eq_(event.mozilla_event, mozilla_event[self.data['mozilla_event']])

        # Ensure event metrics are saved
        metrics = []
        for metric in Metric.objects.filter(event_id=event.id):
            metrics.append((metric.title, metric.outcome))

        for i in range(0, 3):
            title = self.data['metrics-%d-title' % i]
            outcome = self.data['metrics-%d-outcome' % i]
            self.assertTrue((title, outcome) in metrics)

        # Ensure event start/end is saved
        month = self.data['start_form_0_month']
        day = self.data['start_form_0_day']
        year = self.data['start_form_0_year']
        hour = self.data['start_form_1_hour']
        minute = self.data['start_form_1_minute']

        zone = timezone(self.data['timezone'])

        start = datetime.datetime(year, month, day, hour, minute)
        eq_(make_aware(start, zone), event.start)

        month = self.data['end_form_0_month']
        day = self.data['end_form_0_day']
        year = self.data['end_form_0_year']
        hour = self.data['end_form_1_hour']
        minute = self.data['end_form_1_minute']

        end = datetime.datetime(year, month, day, hour, minute)
        eq_(make_aware(end, zone), event.end)

    def test_required_fields(self):
        """Test required fields error handling"""
        c = Client()

        # Login as test-event owner
        c.login(username='rep', password='passwd')

        # Test invalid event date
        invalid_data = self.data.copy()
        invalid_data['end_form_0_year'] = invalid_data['start_form_0_year'] - 1

        response = c.post(self.event_edit_url, invalid_data, follow=True)
        self.assertNotEqual(response.request['PATH_INFO'], self.event_url)

        # Test invalid number of metrics
        invalid_data = self.data.copy()
        invalid_data['metrics-TOTAL_FORMS'] = 1

        invalid_data.pop('metrics-1-title')
        invalid_data.pop('metrics-1-outcome')
        invalid_data.pop('metrics-2-title')
        invalid_data.pop('metrics-2-outcome')

        response = c.post(self.event_edit_url, invalid_data, follow=True)
        self.assertNotEqual(response.request['PATH_INFO'], self.event_url)

        # Test invalid event name, description, venue, city
        fields = ['name', 'description', 'venue', 'city']

        for field in fields:
            invalid_data = self.data.copy()
            invalid_data[field] = ''
            response = c.post(self.event_edit_url, invalid_data, follow=True)
            self.assertNotEqual(response.request['PATH_INFO'], self.event_url)
