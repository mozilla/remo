from django.core import management
from django.core.urlresolvers import reverse
from django.test.client import Client
from nose.tools import eq_
from test_utils import TestCase


class ViewsTest(TestCase):
    """Tests related to Events Views."""
    fixtures = ['demo_users.json', 'demo_events.json']

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
        response = c.get(reverse('events_subscribe_to_event',
                                kwargs={'slug': 'test-event'}),
                         follow=True)
        self.assertTemplateUsed(response, 'main.html',
                                ('Anonymous user is not returned to '
                                 'main.html to login'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning', 'Anonymous user does not get a warning.')

        # Logged in user.
        c.login(username='rep', password='passwd')
        response = c.get(reverse('events_subscribe_to_event',
                                kwargs={'slug': 'test-event'}),
                         follow=True)
        self.assertTemplateUsed(response, 'view_event.html',
                                ('Rep user is not returned to '
                                 'event page after subscribing.'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')

        # Subscribed tries again.
        response = c.get(reverse('events_subscribe_to_event',
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
        response = c.get(reverse('events_unsubscribe_from_event',
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
        response = c.get(reverse('events_unsubscribe_from_event',
                                kwargs={'slug': 'test-event'}),
                         follow=True)
        self.assertTemplateUsed(response, 'view_event.html',
                                ('Rep user is not returned to '
                                 'event page after unsubscribing.'))
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success', 'User does not get a success message.')

        # Subscribed tries again.
        response = c.get(reverse('events_unsubscribe_from_event',
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
            response = c.get(reverse('events_delete_event',
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
