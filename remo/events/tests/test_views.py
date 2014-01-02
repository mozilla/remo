# -*- coding: utf8 -*-
import datetime
from pytz import timezone

from django.conf import settings
from django.contrib.auth.models import User
from django.core import management, mail
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.utils.encoding import iri_to_uri
from django.utils.timezone import make_aware

import mock
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
            'categories': [3, 4, 5, 12, 18, 20],
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
        eq_(m.tags, u'info')

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
        self.assertTemplateUsed(response, 'multi_event_ical_template.ics')
        self.failUnless(response['Content-Type'].startswith('text/calendar'))

    def test_multi_event_ical_export(self):
        """Test multiple event ical export."""
        c = Client()

        # Export all events to iCal
        period = 'all'
        response = c.get(reverse('multiple_event_ical',
                                 kwargs={'period': period}), follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 2)

        # Export past events to iCal
        period = 'past'
        response = c.get(reverse('multiple_event_ical',
                                 kwargs={'period': period}), follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 2)

        # Export future events to iCal
        period = 'future'
        response = c.get(reverse('multiple_event_ical',
                                 kwargs={'period': period}), follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 0)

        # Export custom date range events to iCal
        period = 'custom'
        response = c.get(reverse('multiple_event_ical',
                                 kwargs={'period': period}), follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))

        # Test 'start' and 'end' terms
        start = '2012-06-25'
        end = '2012-06-26'

        response = c.get(reverse('multiple_event_ical',
                                 kwargs={'period': 'custom/start/%s' % start}),
                         follow=True)

        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 2)

        response = c.get(reverse('multiple_event_ical',
                                 kwargs={'period': 'custom/end/%s' % end}),
                         follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))

        response = c.get(reverse('multiple_event_ical',
                                 kwargs={'period': 'custom/start/%s/end/%s' %
                                         (start, end)}),
                         follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 1)

        # Test 'search' query
        term = 'Test event'
        response = c.get(reverse('multiple_event_ical',
                                 kwargs={'period': 'custom/search/%s' % term}),
                         follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 1)

    def test_edit_event(self):
        """Edit event page"""
        c = Client()

        # Login as test-event owner
        c.login(username='rep', password='passwd')

        response = c.post(self.event_edit_url, self.data, follow=True)
        eq_(response.request['PATH_INFO'], self.event_url)

        # Ensure event data are saved
        event = Event.objects.get(name='Test edit event')

        # Ensure times_edited field increments
        eq_(event.times_edited, 1)

        # Test fields with the same name in POST data and models
        excluded = ['planning_pad_url', 'lat', 'lon', 'mozilla_event',
                    'categories']
        for field in set(self.data).difference(set(excluded)):
            if getattr(event, field, None):
                eq_(str(getattr(event, field)), self.data[field])

        # Test excluded fields
        pad_url = self.pad_url + self.pad_prefix + event.slug
        mozilla_event = {'on': True, 'off': False}

        eq_(self.data['categories'], [cat.id
                                      for cat in event.categories.all()])

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

        # Test event cloning
        c = Client()
        c.login(username='rep3', password='passwd')

        event_clone_url = reverse('events_clone_event',
                                  kwargs={'slug': 'test-event'})
        new_event_url = reverse('events_view_event',
                                kwargs={'slug': 'test-edit-event'})

        response = c.post(event_clone_url, self.data, follow=True)
        cloned_event = Event.objects.get(slug='test-edit-event')

        # Test if cloned event is created with the correct slug
        # metrics and categories
        eq_(response.request['PATH_INFO'], new_event_url)
        eq_(Event.objects.all().count(), 3)
        eq_(Metric.objects.all().count(), 7)
        eq_(cloned_event.metrics.all().count(), 3)
        eq_(cloned_event.categories.all().count(), 6)

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

    def test_email_event_attendees(self):
        """Send email to selected event attendees."""
        c = Client()
        c.login(username='rep', password='passwd')

        #Select 2 attendees from list.
        reps = []
        reps.append(User.objects.get(first_name='Koki'))
        reps.append(User.objects.get(first_name='Menis'))

        valid_data = dict()
        for rep in reps:
            field_name = '%s %s <%s>' % (rep.first_name,
                                         rep.last_name,
                                         rep.email)
            valid_data[field_name] = 'True'

        valid_data['subject'] = 'This is the mail subject'
        valid_data['body'] = 'This is the mail subject'
        valid_data['slug'] = 'test-event'

        url = reverse('email_attendees', kwargs={'slug': 'test-event'})
        response = c.post(url, valid_data, follow=True)
        self.assertTemplateUsed(response, 'view_event.html')

        for m in response.context['messages']:
            pass

        eq_(m.tags, u'success')
        eq_(len(mail.outbox), 1)

        email = mail.outbox[0]
        eq_(len(email.to), 2)
        eq_(len(email.cc), 1)

    def test_post_comment_on_event(self):
        """Test post comment on event."""
        c = Client()
        comment = 'This is a new comment'
        # Test anonymous user
        event_view_url = reverse('events_view_event',
                                 kwargs={'slug': 'test-event'})
        response = c.post(event_view_url, {'comment': comment}, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Test authenticated user
        c.login(username='rep3', password='passwd')

        response = c.post(event_view_url, {'comment': comment}, follow=True)
        self.assertTemplateUsed(response, 'view_event.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
        eq_(response.context['request'].POST['comment'], comment)

        event = Event.objects.get(slug='test-event')
        if event.owner.userprofile.receive_email_on_add_event_comment:
            eq_(len(mail.outbox), 1)

    def test_post_delete_event_comment(self):
        """Test delete event comment."""
        c = Client()
        comment_delete = reverse('events_delete_event_comment',
                                 kwargs={'slug': 'multi-event',
                                         'pk': '1'})

        # Test anonymous user
        response = c.post(comment_delete, follow=True)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')

        self.assertTemplateUsed(response, 'main.html')

        # Test authenticated user without delete permission
        # Rep
        c.login(username='rep3', password='passwd')
        response = c.post(comment_delete, follow=True)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        self.assertTemplateUsed(response, 'main.html')

        # Mentor
        c.login(username='mentor', password='passwd')
        response = c.post(comment_delete, follow=True)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        self.assertTemplateUsed(response, 'main.html')

        # Counselor
        c.login(username='counselor', password='passwd')
        response = c.post(comment_delete, follow=True)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        self.assertTemplateUsed(response, 'main.html')

        # Test authenticated user with delete permission
        # Comment owner
        c.login(username='rep', password='passwd')
        response = c.post(comment_delete, follow=True)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')

        self.assertTemplateUsed(response, 'view_event.html')

    def test_post_delete_event_comment_admin(self):
        """Test admin delete event comment."""
        c = Client()
        comment_delete = reverse('events_delete_event_comment',
                                 kwargs={'slug': 'multi-event',
                                         'pk': '1'})
        # Admin
        c.login(username='admin', password='passwd')
        response = c.post(comment_delete, follow=True)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')

        self.assertTemplateUsed(response, 'view_event.html')

    @mock.patch('remo.events.views.iri_to_uri', wraps=iri_to_uri)
    def test_view_redirect_list_events(self, mocked_uri):
        """Test redirect to events list."""
        events_url = '/events/Paris & Orléans'
        response = self.client.get(events_url, follow=True)
        mocked_uri.assert_called_once_with(u'/Paris & Orléans')
        expected_url = '/events/#/Paris%20&%20Orl%C3%A9ans'
        self.assertRedirects(response, expected_url=expected_url,
                             status_code=301, target_status_code=200)
        self.assertTemplateUsed(response, 'list_events.html')
