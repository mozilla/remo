from django.core.urlresolvers import reverse
from django.test.client import Client

from nose.tools import eq_
from test_utils import TestCase

from remo.voting.models import Poll


class ViewsTest(TestCase):
    """Tests related to Voting Views."""
    fixtures = ['demo_users.json', 'demo_voting.json']

    def setUp(self):
        """Initial data for the tests."""
        self.post_data = {'range_poll__1': 1,
                          'range_poll__2': 2,
                          'range_poll__3': 0,
                          'range_poll__4': 3,
                          'range_poll__5': 1,
                          'radio_poll__1': 2}

        self.vote_url = reverse('voting_view_voting',
                                kwargs={'slug': 'current-test-voting'})
        self.view_vote_url = reverse('voting_view_voting',
                                     kwargs={'slug': 'current-test-voting'})

    def test_view_list_votings(self):
        """Get list votings page."""
        c = Client()

        # Get as anonymous user.
        response = c.get(reverse('voting_list_votings'), follow=True)
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')

        # Get as logged in Rep.
        c.login(username='rep', password='passwd')
        response = c.get(reverse('voting_list_votings'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'list_votings.html')

    def test_view_current_voting(self):
        """View a voting."""
        c = Client()

        # Anonymous user.
        response = c.get(self.view_vote_url, follow=True)
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')

        # Logged in user.
        c.login(username='rep', password='passwd')
        response = c.get(self.view_vote_url)
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'vote_voting.html')

        # Logged in as a mozillian user - not valid voting group.
        c.login(username='mozillian1', password='passwd')
        response = c.get(self.view_vote_url, follow=True)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')
        self.assertTemplateUsed(response, 'list_votings.html')

    def test_view_cast_a_vote(self):
        """Cast a vote on a voting."""
        c = Client()
        # Cast a vote as a valid user.
        c.login(username='rep', password='passwd')
        response = c.post(self.vote_url, self.post_data, follow=True)
        self.assertTemplateUsed(response, 'list_votings.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')

        # Ensure that there is a vote for user 'rep'
        poll = Poll.objects.get(name='Current Test Voting')
        eq_(poll.users_voted.filter(username='rep').count(), 1)

        # Cast a vote as a valid user for a second time.
        response = c.post(self.vote_url, self.post_data, follow=True)
        self.assertTemplateUsed(response, 'list_votings.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')
        eq_(poll.users_voted.filter(username='rep').count(), 1)

        # Cast a vote as an invalid user.
        c.login(username='mozillian1', password='passwd')
        response = c.post(self.vote_url, self.post_data, follow=True)
        self.assertTemplateUsed(response, 'list_votings.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')
        eq_(poll.users_voted.filter(username='mozillian1').count(), 0)

    def test_view_voting_results(self):
        """View the results of a voting."""
        c = Client()

        # Anonymous user.
        response = c.get(reverse('voting_view_voting',
                                 kwargs={'slug': 'past-test-voting'}),
                         follow=True)
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')

        # Logged in user.
        c.login(username='rep', password='passwd')
        response = c.get(reverse('voting_view_voting',
                                 kwargs={'slug': 'past-test-voting'}))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_voting.html')

        # Logged in user, invalid voting group.
        c.login(username='mozillian1', password='passwd')
        response = c.get(reverse('voting_view_voting',
                                 kwargs={'slug': 'past-test-voting'}),
                         follow=True)
        self.assertTemplateUsed(response, 'list_votings.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

    def test_view_future_voting(self):
        """View a voting planned to start in the future."""
        c = Client()
        c.login(username='mozillian1', password='passwd')
        response = c.get(reverse('voting_view_voting',
                                 kwargs={'slug': 'future-test-voting'}),
                         follow=True)
        self.assertTemplateUsed(response, 'list_votings.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')
