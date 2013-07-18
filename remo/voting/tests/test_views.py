import pytz
from datetime import datetime

from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.utils.timezone import make_aware

from nose.tools import eq_
from test_utils import TestCase

from remo.voting.models import (Poll, RadioPoll, RadioPollChoice,
                                RangePoll, RangePollChoice)


class ViewsTest(TestCase):
    """Tests related to Voting Views."""
    fixtures = ['demo_users.json', 'demo_voting.json']

    def setUp(self):
        """Initial data for the tests."""
        self.post_data = {'range_poll__1': 1,
                          'range_poll__2': 2,
                          'radio_poll__1': 2}

        self.edit_future_data = {
            'name': u'Test edit voting',
            'description': u'This is a description.',
            'created_by': u'Nikos Koukos :admin',
            'valid_groups': 3,
            'start_form_0_year': 2018,
            'start_form_0_month': 10,
            'start_form_0_day': 01,
            'start_form_1_hour': 07,
            'start_form_1_minute': 00,
            'end_form_0_year': 2018,
            'end_form_0_month': 10,
            'end_form_0_day': 04,
            'end_form_1_hour': 07,
            'end_form_1_minute': 00,
            'range_polls-TOTAL_FORMS': u'1',
            'range_polls-INITIAL_FORMS': u'1',
            'range_polls-MAX_NUM_FORMS': u'1000',
            'range_polls-0-id': u'1',
            'range_polls-0-name': u'Current Range Poll 1',
            '1_range_choices-0-id': u'1',
            '1_range_choices-0-nominee': '6',
            '1_range_choices-0-DELETE': False,
            '1_range_choices-1-id': u'2',
            '1_range_choices-1-nominee': u'7',
            '1_range_choices-1-DELETE': False,
            '1_range_choices-2-id': u'',
            '1_range_choices-2-nominee': u'',
            '1_range_choices-2-DELETE': False,
            '1_range_choices-TOTAL_FORMS': u'3',
            '1_range_choices-INITIAL_FORMS': u'2',
            '1_range_choices-TOTAL_FORMS': u'1000',
            'radio_polls-0-id': u'1',
            'radio_polls-0-question': u'Radio Poll Example 2 - Question 1',
            'radio_polls-TOTAL_FORMS': u'1',
            'radio_polls-INITIAL_FORMS': u'1',
            'radio_polls-MAX_NUM_FORMS': u'1000',
            '1_radio_choices-TOTAL_FORMS': u'2',
            '1_radio_choices-INITIAL_FORMS': u'2',
            '1_radio_choices-MAX_NUM_FORMS': u'1000',
            '1_radio_choices-0-id': u'1',
            '1_radio_choices-0-answer': u'Radio Poll Example 2 - Answer 1',
            '1_radio_choices-0-DELETE': False,
            '1_radio_choices-1-id': u'2',
            '1_radio_choices-1-answer': u'Radio Poll Example 2 - Answer 2',
            '1_radio_choices-1-DELETE': False}

        self.edit_current_data = {
            'name': u'Test edit voting',
            'description': u'This is a description.',
            'created_by': u'Nikos Koukos :admin',
            'valid_groups': 3,
            'start_form_0_year': 2011,
            'end_form_0_year': 2018,
            'end_form_0_month': 10,
            'end_form_0_day': 04,
            'end_form_1_hour': 07,
            'end_form_1_minute': 00}

        self.vote_url = reverse('voting_view_voting',
                                kwargs={'slug': 'current-test-voting'})
        self.view_vote_url = reverse('voting_view_voting',
                                     kwargs={'slug': 'current-test-voting'})
        self.current_voting_edit_url = (
            reverse('voting_edit_voting',
                    kwargs=({'slug': 'current-test-voting'})))
        self.future_voting_edit_url = (
            reverse('voting_edit_voting',
                    kwargs={'slug': 'future-test-voting'}))
        # Give permissions to admin group
        group = Group.objects.get(name='Admin')
        permissions = Permission.objects.filter(name__icontains='poll')
        for perm in permissions:
            group.permissions.add(perm)

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
        c.login(username='rep', password='passwd')
        response = c.get(reverse('voting_view_voting',
                                 kwargs={'slug': 'future-test-voting'}),
                         follow=True)
        self.assertTemplateUsed(response, 'list_votings.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')

        # View future voting as admin
        c.login(username='admin', password='passwd')
        response = c.get(reverse('voting_view_voting',
                                 kwargs={'slug': 'future-test-voting'}),
                         follow=True)
        self.assertTemplateUsed(response, 'edit_voting.html')

    def test_view_edit_future_voting(self):
        """Edit future voting test."""
        c = Client()

        # Logged in as a non-admin user.
        c.login(username='rep', password='passwd')
        response = c.post(self.future_voting_edit_url, self.edit_future_data,
                          follow=True)
        eq_(response.request['PATH_INFO'], '/')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Logged in as administrator.
        c.login(username='admin', password='passwd')
        response = c.post(self.future_voting_edit_url, self.edit_future_data,
                          follow=True)
        eq_(response.request['PATH_INFO'], self.future_voting_edit_url)

        # Ensure voting data get saved.
        poll = Poll.objects.get(name='Test edit voting')

        # Test fields with the same name in POST data and models.
        excluded = ['valid_groups']
        for field in set(self.edit_future_data).difference(set(excluded)):
            if getattr(poll, field, None):
                eq_(str(getattr(poll, field)), self.edit_future_data[field])

        # Test excluded fields.
        eq_(self.edit_future_data['valid_groups'], poll.valid_groups.id)

        # Ensure Range/Radio Polls are saved.
        range_poll = RangePoll.objects.get(poll_id=poll.id)

        nominees = []
        for choice in (RangePollChoice.objects
                       .filter(range_poll_id=range_poll.id)):
            nominees.append(choice.nominee.id)

        for i in range(0, 2):
            nominee = int((self.
                           edit_future_data['1_range_choices-%d-nominee' % i]))
            self.assertTrue(nominee in nominees)

        name = self.edit_future_data['range_polls-0-name']
        eq_(name, range_poll.name)

        radio_poll = RadioPoll.objects.get(poll_id=poll.id)

        answers = []
        for choice in (RadioPollChoice.objects
                       .filter(radio_poll_id=radio_poll.id)):
            answers.append(choice.answer)

        for i in range(0, 2):
            answer = self.edit_future_data['1_radio_choices-%d-answer' % i]
            self.assertTrue(answer in answers)

        question = self.edit_future_data['radio_polls-0-question']
        eq_(question, radio_poll.question)

        # Ensure voting start/end is saved.
        month = self.edit_future_data['start_form_0_month']
        day = self.edit_future_data['start_form_0_day']
        year = self.edit_future_data['start_form_0_year']
        hour = self.edit_future_data['start_form_1_hour']
        minute = self.edit_future_data['start_form_1_minute']

        start = datetime(year, month, day, hour, minute)
        eq_(make_aware(start, pytz.UTC), poll.start)

        month = self.edit_future_data['end_form_0_month']
        day = self.edit_future_data['end_form_0_day']
        year = self.edit_future_data['end_form_0_year']
        hour = self.edit_future_data['end_form_1_hour']
        minute = self.edit_future_data['end_form_1_minute']

        end = datetime(year, month, day, hour, minute)
        eq_(make_aware(end, pytz.UTC), poll.end)

    def test_view_edit_current_voting(self):
        """Test current voting test."""
        c = Client()

        # Logged in as a non-admin user.
        c.login(username='rep', password='passwd')
        response = c.post(self.current_voting_edit_url,
                          self.edit_current_data, follow=True)
        eq_(response.request['PATH_INFO'], '/')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Logged in as administrator.
        c.login(username='admin', password='passwd')
        response = c.post(self.current_voting_edit_url,
                          self.edit_current_data, follow=True)
        eq_(response.request['PATH_INFO'], self.current_voting_edit_url)

        # Ensure voting data get saved.
        poll = Poll.objects.get(name='Test edit voting')

        # Test fields with the same name in POST data and models.
        excluded = ['valid_groups']
        for field in set(self.edit_current_data).difference(set(excluded)):
            if getattr(poll, field, None):
                eq_(str(getattr(poll, field)), self.edit_current_data[field])

        # Test excluded fields.
        eq_(self.edit_current_data['valid_groups'], poll.valid_groups.id)

        # Ensure voting end is saved.
        month = self.edit_current_data['end_form_0_month']
        day = self.edit_current_data['end_form_0_day']
        year = self.edit_current_data['end_form_0_year']
        hour = self.edit_current_data['end_form_1_hour']
        minute = self.edit_current_data['end_form_1_minute']

        end = datetime(year, month, day, hour, minute)
        eq_(make_aware(end, pytz.UTC), poll.end)

        start_year = self.edit_current_data['start_form_0_year']
        self.assertNotEqual(poll.start.year, start_year)

    def test_view_edit_voting(self):
        """Test view edit voting."""
        c = Client()

        # Anonymous user
        response = c.get(self.current_voting_edit_url, follow=True)
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')

        # Logged in user.
        c.login(username='rep', password='passwd')
        response = c.get(self.current_voting_edit_url, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Logged in as admin
        c.login(username='admin', password='passwd')
        response = c.get(self.current_voting_edit_url)
        self.assertTemplateUsed(response, 'edit_voting.html')

    def test_view_delete_voting(self):
        """Test delete voting."""
        c = Client()

        # Anonymous user.
        response = c.get(reverse('voting_delete_voting',
                                 kwargs={'slug': 'current-test-voting'}),
                         follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')

        # Valid user with no permissions.
        c.login(username='rep3', password='passwd')
        response = c.get(reverse('voting_delete_voting',
                                 kwargs={'slug': 'current-test-voting'}),
                         follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Login as administrator.
        c.login(username='admin', password='passwd')
        response = c.post(reverse('voting_delete_voting',
                                  kwargs={'slug': 'current-test-voting'}),
                          follow=True)
        self.assertTemplateUsed(response, 'list_votings.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
