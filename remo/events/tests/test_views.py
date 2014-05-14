# -*- coding: utf-8 -*-
import datetime
import mock

from django.core import mail
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.encoding import iri_to_uri
from django.utils.timezone import make_aware, now

from mock import ANY
from nose.tools import eq_, ok_
from pytz import timezone
from test_utils import TestCase

from remo.base.tests import requires_login, requires_permission
from remo.events.models import Event, EventComment, EventMetricOutcome
from remo.events.tests import (AttendanceFactory, EventCommentFactory,
                               EventFactory, EventGoalFactory,
                               EventMetricFactory)
from remo.profiles.tests import FunctionalAreaFactory, UserFactory


class ViewsTest(TestCase):
    """Tests related to Events Views."""

    def setUp(self):

        categories = FunctionalAreaFactory.create_batch(3)
        goals = EventGoalFactory.create_batch(3)
        metrics = EventMetricFactory.create_batch(3)

        self.data = {
            'name': u'Test edit event',
            'description': u'This is a description',
            'external_link': '',
            'categories': [x.id for x in categories],
            'goals': [x.id for x in goals],
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
            'mozilla_event': u'on',
            'estimated_attendance': u'10',
            'extra_content': u'This is extra content',
            'planning_pad_url': u'',
            'hashtag': u'#testevent',
            'swag_bug_form': u'',
            'budget_bug_form': u'',
            'eventmetricoutcome_set-0-id': '',
            'eventmetricoutcome_set-0-metric': metrics[0].id,
            'eventmetricoutcome_set-0-outcome': 100,
            'eventmetricoutcome_set-1-id': '',
            'eventmetricoutcome_set-1-metric': metrics[1].id,
            'eventmetricoutcome_set-1-outcome': 10,
            'eventmetricoutcome_set-TOTAL_FORMS': 2,
            'eventmetricoutcome_set-INITIAL_FORMS': 0}

        self.event_edit_url = reverse('events_edit_event',
                                      kwargs={'slug': 'test-event'})
        self.event_url = reverse('events_view_event',
                                 kwargs={'slug': 'test-event'})

    def test_view_events_list(self):
        """Get list events page."""
        response = self.client.get(reverse('events_list_events'))
        self.assertTemplateUsed(response, 'list_events.html')

    def test_view_event_page(self):
        """Get view event page."""
        EventFactory.create(slug='test-event')
        response = self.client.get(self.event_url)
        self.assertTemplateUsed(response, 'view_event.html')

    @mock.patch('django.contrib.messages.error')
    def test_post_comment_on_event_unauthed(self, mock_error):
        """Test post comment on event unauthorized."""
        comment = 'This is a new comment'
        EventFactory.create(slug='test-event')
        response = self.client.post(self.event_url, {'comment': comment},
                                    follow=True)
        self.assertTemplateUsed(response, 'main.html')
        mock_error.assert_called_with(ANY, 'Permission Denied')

    @mock.patch('django.contrib.messages.success')
    def test_post_comment_on_event_rep(self, mock_success):
        """Test post comment on event as rep."""
        # Test authenticated user
        event = EventFactory.create(slug='test-event')
        kwargs = {'groups': ['Rep'],
                  'userprofile__receive_email_on_add_event_comment': True}
        user = UserFactory.create(**kwargs)
        comment = 'This is a new comment'

        self.client.login(username=user.username, password='passwd')
        response = self.client.post(self.event_url, {'comment': comment},
                                    follow=True)
        comment = event.eventcomment_set.get(user=user)

        self.assertTemplateUsed(response, 'view_event.html')
        mock_success.assert_called_with(ANY, 'Comment saved')
        eq_(comment.comment, 'This is a new comment')

        eq_(len(mail.outbox), 1)

    @requires_login()
    def test_post_delete_event_comment_unauth(self):
        """Test unauthorized delete event comment."""
        event = EventFactory.create(slug='test-event')
        user = UserFactory.create(groups=['Rep'])
        comment = EventCommentFactory.create(event=event, user=user)
        comment_delete = reverse('events_delete_event_comment',
                                 kwargs={'slug': 'test-event',
                                         'pk': comment.id})
        self.client.post(comment_delete, {'comment': comment}, follow=True)
        ok_(EventComment.objects.filter(pk=comment.id).exists())

    @requires_permission()
    def test_post_delete_event_comment_user_no_perms(self):
        """Test delete event comment as rep without delete permissions."""
        event = EventFactory.create(slug='test-event')
        user = UserFactory.create(groups=['Rep'])
        comment = EventCommentFactory.create(event=event)
        comment_delete = reverse('events_delete_event_comment',
                                 kwargs={'slug': 'test-event',
                                         'pk': comment.id})
        self.client.login(username=user.username, password='passwd')
        self.client.post(comment_delete, follow=True)
        ok_(EventComment.objects.filter(pk=comment.id).exists())

    @mock.patch('django.contrib.messages.success')
    def test_post_delete_event_comment_owner(self, mock_success):
        """ Test delete event comment as event comment owner."""
        event = EventFactory.create(slug='test-event')
        user = UserFactory.create(groups=['Rep'])
        comment = EventCommentFactory.create(event=event, user=user)
        comment_delete = reverse('events_delete_event_comment',
                                 kwargs={'slug': 'test-event',
                                         'pk': comment.id})
        self.client.login(username=user.username, password='passwd')
        response = self.client.post(comment_delete, follow=True)

        mock_success.assert_called_with(ANY, 'Comment successfully deleted.')
        ok_(not EventComment.objects.filter(pk=comment.id).exists())
        self.assertTemplateUsed(response, 'view_event.html')

    @mock.patch('django.contrib.messages.success')
    def test_post_delete_event_comment_admin(self, mock_success):
        """Test delete event comment as admin."""
        event = EventFactory.create(slug='test-event')
        user = UserFactory.create(groups=['Admin'])
        comment = EventCommentFactory.create(event=event)
        comment_delete = reverse('events_delete_event_comment',
                                 kwargs={'slug': 'test-event',
                                         'pk': comment.id})
        self.client.login(username=user.username, password='passwd')
        response = self.client.post(comment_delete, follow=True)
        mock_success.assert_called_with(ANY, 'Comment successfully deleted.')
        self.assertTemplateUsed(response, 'view_event.html')

    def test_subscription_management_no_perms(self):
        """Subscribe to event without permissions."""
        response = self.client.post(reverse('events_subscribe_to_event',
                                            kwargs={'slug': 'test-event'}),
                                    follow=True)
        self.assertTemplateUsed(response, 'main.html',
                                ('Anonymous user is not returned to '
                                 'main.html to login'))

    @mock.patch('django.contrib.messages.info')
    def test_subscription_management_rep(self, mock_info):
        """ Subscribe rep to event."""
        user = UserFactory.create(groups=['Rep'])
        EventFactory.create(slug='test-event')
        self.client.login(username=user.username, password='passwd')
        response = self.client.post(reverse('events_subscribe_to_event',
                                            kwargs={'slug': 'test-event'}),
                                    follow=True)
        self.assertTemplateUsed(response, 'view_event.html',
                                ('Rep user is not returned to '
                                 'event page after subscribing.'))
        ok_(mock_info.called, 'messages.info() was not called')

    @mock.patch('django.contrib.messages.warning')
    def test_subscription_management_subscribed(self, mock_warning):
        """ Test subscribe already subscribed user."""
        user = UserFactory.create(groups=['Rep'])
        event = EventFactory.create(slug='test-event')
        AttendanceFactory.create(user=user, event=event)
        self.client.login(username=user.username, password='passwd')
        response = self.client.post(reverse('events_subscribe_to_event',
                                            kwargs={'slug': 'test-event'}),
                                    follow=True)
        self.assertTemplateUsed(response, 'view_event.html',
                                ('Rep user is not returned to '
                                 'event page after subscribing.'))
        msg = 'You are already subscribed to this event.'
        mock_warning.assert_called_with(ANY, msg)

    @requires_login()
    def test_unsubscribe_from_event_unauth(self):
        """Unsubscribe from event anonymous user."""

        EventFactory.create(slug='test-event')
        self.client.post(reverse('events_unsubscribe_from_event',
                                 kwargs={'slug': 'test-event'}), follow=True)

    @mock.patch('django.contrib.messages.success')
    def test_unsubscribe_from_event_subscribed(self, mock_success):
        """Test unsubscribe from event subscribed user."""
        user = UserFactory.create(groups=['Rep'])
        event = EventFactory.create(slug='test-event')
        AttendanceFactory.create(user=user, event=event)
        self.client.login(username=user.username, password='passwd')
        response = self.client.post(reverse('events_unsubscribe_from_event',
                                            kwargs={'slug': 'test-event'}),
                                    follow=True)
        self.assertTemplateUsed(response, 'view_event.html',
                                ('Rep user is not returned to '
                                 'event page after unsubscribing.'))
        msg = 'You have unsubscribed from this event.'
        mock_success.assert_called_with(ANY, msg)

    @mock.patch('django.contrib.messages.warning')
    def test_unsubscribe_from_event_unsubscribed(self, mock_warning):
        """Test unsubscribe from event without subscription."""
        user = UserFactory.create(groups=['Rep'])
        EventFactory.create(slug='test-event')

        self.client.login(username=user.username, password='passwd')
        response = self.client.post(reverse('events_unsubscribe_from_event',
                                            kwargs={'slug': 'test-event'}),
                                    follow=True)
        self.assertTemplateUsed(response, 'view_event.html',
                                ('Rep user is not returned to '
                                 'event page after unsubscribing.'))
        msg = 'You are not subscribed to this event.'
        mock_warning.assert_called_with(ANY, msg)

    @requires_login()
    def test_delete_event_unauthorized(self):
        """Test delete event unauthorized."""
        event = EventFactory.create(slug='test-event')
        self.client.get(reverse('events_delete_event',
                                kwargs={'slug': 'test-event'}), follow=True)
        ok_(Event.objects.filter(pk=event.id).exists())

    def test_delete_event_no_permissions(self):
        """Test delete event no permissions."""
        user = UserFactory.create(groups=['Rep'])
        event = EventFactory.create(slug='test-event')
        self.client.login(username=user.username, password='passwd')
        response = self.client.get(reverse('events_delete_event',
                                           kwargs={'slug': 'test-event'}),
                                   follow=True)
        self.assertTemplateUsed(response, 'main.html',
                                ('Rep is not returned to main.html.'))
        ok_(Event.objects.filter(pk=event.id).exists())

    @mock.patch('django.contrib.messages.success')
    def test_delete_event_owner(self, mock_success):
        """Test delete event with owner permissions."""
        user = UserFactory.create(groups=['Rep'])
        event = EventFactory.create(slug='test-event', owner=user)
        self.client.login(username=user.username, password='passwd')

        response = self.client.post(reverse('events_delete_event',
                                            kwargs={'slug': 'test-event'}),
                                    follow=True)
        self.assertTemplateUsed(response, 'list_events.html',
                                ('User %s not returned to '
                                 'main.html.' % user))
        ok_(not Event.objects.filter(pk=event.id).exists())
        mock_success.assert_called_with(ANY, 'Event successfully deleted.')

    @mock.patch('django.contrib.messages.success')
    def test_delete_event_mentor(self, mock_success):
        """Test delete event with mentor permissions."""
        user = UserFactory.create(groups=['Mentor'])
        event = EventFactory.create(slug='test-event')
        self.client.login(username=user.username, password='passwd')
        response = self.client.post(reverse('events_delete_event',
                                            kwargs={'slug': 'test-event'}),
                                    follow=True)
        self.assertTemplateUsed(response, 'list_events.html',
                                ('User %s not returned to '
                                 'main.html.' % user))
        ok_(not Event.objects.filter(pk=event.id).exists())
        mock_success.assert_called_with(ANY, 'Event successfully deleted.')

    @mock.patch('django.contrib.messages.success')
    def test_delete_event_councelor(self, mock_success):
        """Test delete event with councelor permissions."""
        user = UserFactory.create(groups=['Council'])
        event = EventFactory.create(slug='test-event')
        self.client.login(username=user.username, password='passwd')
        response = self.client.post(reverse('events_delete_event',
                                            kwargs={'slug': 'test-event'}),
                                    follow=True)
        self.assertTemplateUsed(response, 'list_events.html',
                                ('User %s not returned to '
                                 'main.html.' % user))
        ok_(not Event.objects.filter(pk=event.id).exists())
        mock_success.assert_called_with(ANY, 'Event successfully deleted.')

    @mock.patch('django.contrib.messages.success')
    def test_delete_event_admin(self, mock_success):
        """Test delete event with admin permissions."""
        user = UserFactory.create(groups=['Admin'])
        event = EventFactory.create(slug='test-event')
        self.client.login(username=user.username, password='passwd')
        response = self.client.post(reverse('events_delete_event',
                                            kwargs={'slug': 'test-event'}),
                                    follow=True)
        self.assertTemplateUsed(response, 'list_events.html',
                                ('User %s not returned to '
                                 'main.html.' % user))
        ok_(not Event.objects.filter(pk=event.id).exists())
        mock_success.assert_called_with(ANY, 'Event successfully deleted.')

    def test_converted_visitors(self):
        """Test converted visitors counter."""
        event = EventFactory.create(slug='test-event')
        converted_visitors = event.converted_visitors + 1
        self.client.post(reverse('events_count_converted_visitors',
                                 kwargs={'slug': 'test-event'}),
                         follow=True)
        event = Event.objects.get(slug='test-event')
        eq_(event.converted_visitors, converted_visitors)

    def test_export_event_to_ical(self):
        """Test ical export."""
        EventFactory.create(slug='test-event')
        response = self.client.get(reverse('events_icalendar_event',
                                           kwargs={'slug': 'test-event'}))
        self.assertTemplateUsed(response, 'multi_event_ical_template.ics')
        self.failUnless(response['Content-Type'].startswith('text/calendar'))

    def test_multi_event_ical_export(self):
        """Test multiple event ical export."""
        EventFactory.create_batch(2)

        # Export all events to iCal
        period = 'all'
        response = self.client.get(reverse('multiple_event_ical',
                                           kwargs={'period': period}),
                                   follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 2)

    def test_multi_event_ical_export_past(self):
        """Test multiple past event ical export."""
        EventFactory.create_batch(2)

        # Export past events to iCal
        period = 'past'
        response = self.client.get(reverse('multiple_event_ical',
                                           kwargs={'period': period}),
                                   follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 2)

    def test_multi_event_ical_export_future(self):
        """Test multiple past event ical export."""
        start = now() + datetime.timedelta(days=1)
        end = now() + datetime.timedelta(days=2)
        EventFactory.create_batch(2, start=start, end=end)

        # Export future events to iCal
        period = 'future'
        response = self.client.get(reverse('multiple_event_ical',
                                           kwargs={'period': period}),
                                   follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 2)

    def test_multi_event_ical_export_custom(self):
        """Test multiple event ical export with custom date."""
        event_start = now() + datetime.timedelta(days=1)
        event_end = now() + datetime.timedelta(days=2)
        EventFactory.create_batch(2, start=event_start, end=event_end)
        period = 'custom'
        response = self.client.get(reverse('multiple_event_ical',
                                           kwargs={'period': period}),
                                   follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))

        start = (event_start - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        end = (event_end + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        query = 'custom/start/%s/end/%s' % (start, end)
        response = self.client.get(reverse('multiple_event_ical',
                                           kwargs={'period': query}),
                                   follow=True)

        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 2)

    def test_multi_event_ical_export_search(self):
        """Test multiple past event ical export."""

        EventFactory.create(name='Test event')

        # Test 'search' query
        term = 'Test event'
        search = 'custom/search/%s' % term
        response = self.client.get(reverse('multiple_event_ical',
                                           kwargs={'period': search}),
                                   follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))
        eq_(len(response.context['events']), 1)

    def test_multi_event_ical_export_extra_chars(self):
        """Test multi event ical export with extra chars.

        See bug 956271 for details.
        """

        url = '/events/period/future/search/méxico.!@$%&*()/ical/'
        response = self.client.get(url, follow=True)
        self.failUnless(response['Content-Type'].startswith('text/calendar'))

    @mock.patch('django.contrib.messages.success')
    def test_post_create_event_rep(self, mock_success):
        """Test create new event with rep permissions."""
        user = UserFactory.create(groups=['Rep'])
        self.client.login(username=user.username, password='passwd')
        response = self.client.post(self.event_edit_url, self.data,
                                    follow=True)
        mock_success.assert_called_with(ANY, 'Event successfully created.')
        eq_(mock_success.call_count, 1)
        eq_(response.request['PATH_INFO'], self.event_url)
        event = Event.objects.get(name='Test edit event')
        eq_(event.times_edited, 1)
        eq_(event.owner, user)

    def test_get_create_event_rep(self):
        """Test get create event page with rep permissions."""
        user = UserFactory.create(groups=['Rep'])
        self.client.login(username=user.username, password='passwd')
        url = reverse('events_new_event')
        response = self.client.get(url, follow=True)
        eq_(response.request['PATH_INFO'], url)
        ok_(response.context['creating'])
        ok_(not response.context['event_form'].editable_owner)
        self.assertTemplateUsed('edit_event.html')

    def test_get_edit_event_rep(self):
        """Test get event edit page with rep permissions."""
        user = UserFactory.create(groups=['Rep'])
        EventFactory.create(slug='test-event')
        self.client.login(username=user.username, password='passwd')
        response = self.client.get(self.event_edit_url, follow=True)
        eq_(response.request['PATH_INFO'], self.event_edit_url)
        ok_(not response.context['creating'])
        ok_(not response.context['event_form'].editable_owner)
        eq_(response.context['event'].slug, 'test-event')
        self.assertTemplateUsed('edit_event.html')

    @mock.patch('django.contrib.messages.success')
    def test_get_edit_event_admin(self, mock_success):
        """Test get event edit page with admin permissions"""
        user = UserFactory.create(groups=['Admin'])
        EventFactory.create(slug='test-event')
        self.client.login(username=user.username, password='passwd')
        response = self.client.get(self.event_edit_url, follow=True)
        eq_(response.request['PATH_INFO'], self.event_edit_url)
        ok_(not response.context['creating'])
        ok_(response.context['event_form'].editable_owner)
        eq_(response.context['event'].slug, 'test-event')
        self.assertTemplateUsed('edit_event.html')

    @mock.patch('django.contrib.messages.success')
    @override_settings(ETHERPAD_URL="http://example.com")
    @override_settings(ETHERPAD_PREFIX="remo-")
    def test_edit_event_rep(self, mock_success):
        """Test edit event with rep permissions."""
        user = UserFactory.create(groups=['Rep'])
        event = EventFactory.create(slug='test-event', owner=user)
        times_edited = event.times_edited
        self.client.login(username=user.username, password='passwd')
        response = self.client.post(self.event_edit_url, self.data,
                                    follow=True)
        mock_success.assert_called_with(ANY, 'Event successfully updated.')
        eq_(mock_success.call_count, 1)
        eq_(response.request['PATH_INFO'], self.event_url)
        event = Event.objects.get(name='Test edit event')
        eq_(event.times_edited, times_edited + 1)
        eq_(event.owner, user)

        # TODO: replace the following section with form tests

        # Test fields with the same name in POST data and models
        excluded = ['planning_pad_url', 'lat', 'lon', 'mozilla_event',
                    'categories', 'goals']
        for field in set(self.data).difference(set(excluded)):
            if getattr(event, field, None):
                eq_(str(getattr(event, field)), self.data[field])

        # Test excluded fields
        pad_url = 'http://example.com/remo-' + event.slug
        mozilla_event = {'on': True, 'off': False}

        eq_(set(self.data['categories']),
            set(event.categories.values_list('id', flat=True)))
        eq_(set(self.data['goals']),
            set(event.goals.values_list('id', flat=True)))

        eq_(event.planning_pad_url, pad_url)
        eq_(event.lat, self.data['lat'])
        eq_(event.lon, self.data['lon'])
        eq_(event.mozilla_event, mozilla_event[self.data['mozilla_event']])

        # Ensure event metrics are saved
        metrics = (EventMetricOutcome.objects.filter(event=event)
                   .values_list('metric__id', 'outcome'))

        for i in range(0, 2):
            metric = self.data['eventmetricoutcome_set-%d-metric' % i]
            outcome = self.data['eventmetricoutcome_set-%d-outcome' % i]
            self.assertTrue((metric, outcome) in metrics)

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

        # TODO: replace the following test with form tests
        # Login as test-event owner
        user = UserFactory.create(groups=['Rep'])
        self.client.login(username=user.username, password='passwd')

        # Test invalid event date
        invalid_data = self.data.copy()
        invalid_data['end_form_0_year'] = invalid_data['start_form_0_year'] - 1

        response = self.client.post(self.event_edit_url, invalid_data,
                                    follow=True)
        self.assertNotEqual(response.request['PATH_INFO'], self.event_url)

        # Test invalid number of metrics
        invalid_data = self.data.copy()

        invalid_data['eventmetricoutcome_set-TOTAL_FORMS'] = 1
        invalid_data.pop('eventmetricoutcome_set-0-id')
        invalid_data.pop('eventmetricoutcome_set-0-metric')
        invalid_data.pop('eventmetricoutcome_set-0-outcome')
        invalid_data.pop('eventmetricoutcome_set-1-id')
        invalid_data.pop('eventmetricoutcome_set-1-metric')
        invalid_data.pop('eventmetricoutcome_set-1-outcome')

        response = self.client.post(self.event_edit_url, invalid_data,
                                    follow=True)
        self.assertNotEqual(response.request['PATH_INFO'], self.event_url)

        # Test invalid event name, description, venue, city
        fields = ['name', 'description', 'venue', 'city']

        for field in fields:
            invalid_data = self.data.copy()
            invalid_data[field] = ''
            response = self.client.post(self.event_edit_url, invalid_data,
                                        follow=True)
            self.assertNotEqual(response.request['PATH_INFO'], self.event_url)

    @mock.patch('django.contrib.auth.models.User.has_perm')
    def test_edit_event_page_no_delete_perms(self, mock_perm):
        """Test view edit event page without delete permissions."""
        user = UserFactory.create(groups=['Admin'])
        EventFactory.create(slug='test-event')
        mock_perm.side_effect = [True, False]
        self.client.login(username=user.username, password='passwd')
        response = self.client.get(self.event_edit_url, follow=True)
        eq_(response.request['PATH_INFO'], self.event_edit_url)
        ok_(not response.context['creating'])
        ok_(response.context['event_form'].editable_owner)
        eq_(response.context['event'].slug, 'test-event')
        ok_(not response.context['can_delete_event'])

    @mock.patch('django.contrib.messages.success')
    def test_clone_event_rep(self, mock_success):
        """Test clone event with rep permissions."""
        user = UserFactory.create(groups=['Rep'])
        self.client.login(username=user.username, password='passwd')
        event_clone_url = reverse('events_clone_event',
                                  kwargs={'slug': 'test-event'})
        response = self.client.post(event_clone_url, self.data, follow=True)
        mock_success.assert_called_with(ANY, 'Event successfully created.')
        eq_(mock_success.call_count, 1)
        event = Event.objects.get(name='Test edit event', owner=user)
        cloned_event_url = reverse('events_view_event',
                                   kwargs={'slug': event.slug})
        eq_(event.times_edited, 1)
        eq_(response.request['PATH_INFO'], cloned_event_url)

    @mock.patch('django.contrib.messages.success')
    def test_email_event_attendees(self, mock_success):
        """Send email to selected event attendees."""
        user = UserFactory.create(groups=['Rep'])
        event = EventFactory.create(slug='test-event', owner=user)
        AttendanceFactory.create_batch(3, event=event)
        self.client.login(username=user.username, password='passwd')
        reps = event.attendees.all()
        valid_data = dict()
        for rep in reps:
            field_name = '%s' % rep.id
            valid_data[field_name] = 'True'

        valid_data['subject'] = 'This is the mail subject'
        valid_data['body'] = 'This is the mail subject'
        valid_data['slug'] = 'test-event'

        url = reverse('email_attendees', kwargs={'slug': 'test-event'})
        response = self.client.post(url, valid_data, follow=True)
        self.assertTemplateUsed(response, 'view_event.html')

        mock_success.assert_called_with(ANY, 'Email sent successfully.')
        eq_(len(mail.outbox), 4)

        for i in range(0, len(mail.outbox)):
            eq_(len(mail.outbox[i].cc), 1)
            eq_(len(mail.outbox[i].to), 1)

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
