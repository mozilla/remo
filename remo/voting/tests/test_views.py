import pytz
from datetime import datetime, timedelta

from django.db.models.signals import post_save
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.test.client import Client, RequestFactory
from django.utils.timezone import make_aware, now

import mock
from factory.django import mute_signals
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase, requires_login, requires_permission
from remo.profiles.tests import UserFactory
from remo.remozilla.models import Bug
from remo.remozilla.tests import BugFactory
from remo.voting.models import (Poll, PollComment, RadioPoll, RadioPollChoice,
                                RangePoll, RangePollChoice)
from remo.voting.tests import (PollCommentFactory, PollFactory, RadioPollFactory,
                               RadioPollChoiceFactory, RangePollFactory, RangePollChoiceFactory)
from remo.voting.views import view_voting


class ViewsTest(RemoTestCase):
    """Tests related to Voting Views."""

    def setUp(self):
        """Initial data for the tests."""
        self.nominee1, self.nominee2, self.nominee3 = UserFactory.create_batch(3, groups=['Rep'])
        self.rep = UserFactory.create(groups=['Rep'])
        self.admin = UserFactory.create(groups=['Admin', 'Rep'])
        self.mozillian = UserFactory.create(groups=['Mozillians'])
        poll_start = now() + timedelta(days=5)
        self.admin_group = Group.objects.get(name='Admin')
        self.rep_group = Group.objects.get(name='Rep')
        self.poll = PollFactory.create(valid_groups=self.admin_group,
                                       start=poll_start,
                                       end=poll_start + timedelta(days=10),
                                       comments_allowed=False)
        self.range_poll = RangePollFactory(poll=self.poll)
        self.range_poll_choice1 = RangePollChoiceFactory(range_poll=self.range_poll,
                                                         nominee=self.nominee1)
        self.range_poll_choice2 = RangePollChoiceFactory(range_poll=self.range_poll,
                                                         nominee=self.nominee2)
        self.radio_poll = RadioPollFactory(poll=self.poll)
        self.radio_poll_choice1, self.radio_poll_choice2 = RadioPollChoiceFactory.create_batch(
            2, radio_poll=self.radio_poll)

        self.post_data = {'range_poll__1': 1,
                          'range_poll__2': 2,
                          'radio_poll__1': 2}

        self.edit_future_data = {
            'name': u'Test edit voting',
            'description': u'This is a description.',
            'created_by': self.poll.created_by.id,
            'valid_groups': self.admin_group.id,
            'start_form_0_year': now().year + 1,
            'start_form_0_month': 10,
            'start_form_0_day': 1,
            'start_form_1_hour': 7,
            'start_form_1_minute': 00,
            'end_form_0_year': now().year + 1,
            'end_form_0_month': 10,
            'end_form_0_day': 4,
            'end_form_1_hour': 7,
            'end_form_1_minute': 00,
            'range_polls-TOTAL_FORMS': u'1',
            'range_polls-INITIAL_FORMS': u'1',
            'range_polls-MAX_NUM_FORMS': u'1000',
            'range_polls-0-id': self.range_poll.id,
            'range_polls-0-name': u'Current Range Poll 1',
            '{0}_range_choices-0-id'.format(self.range_poll.id): self.range_poll_choice1.id,
            '{0}_range_choices-0-nominee'.format(self.range_poll.id): self.nominee1.id,
            '{0}_range_choices-0-DELETE'.format(self.range_poll.id): False,
            '{0}_range_choices-1-id'.format(self.range_poll.id): self.range_poll_choice2.id,
            '{0}_range_choices-1-nominee'.format(self.range_poll.id): self.nominee2.id,
            '{0}_range_choices-1-DELETE'.format(self.range_poll.id): False,
            '{0}_range_choices-2-id'.format(self.range_poll.id): u'',
            '{0}_range_choices-2-nominee'.format(self.range_poll.id): self.nominee3.id,
            '{0}_range_choices-2-DELETE'.format(self.range_poll.id): False,
            '{0}_range_choices-TOTAL_FORMS'.format(self.range_poll.id): u'3',
            '{0}_range_choices-INITIAL_FORMS'.format(self.range_poll.id): u'2',
            '{0}_range_choices-TOTAL_FORMS'.format(self.range_poll.id): u'1000',
            'radio_polls-0-id': self.radio_poll.id,
            'radio_polls-0-question': u'Radio Poll - Question 1',
            'radio_polls-TOTAL_FORMS': u'1',
            'radio_polls-INITIAL_FORMS': u'1',
            'radio_polls-MAX_NUM_FORMS': u'1000',
            '{0}_radio_choices-TOTAL_FORMS'.format(self.radio_poll.id): u'2',
            '{0}_radio_choices-INITIAL_FORMS'.format(self.radio_poll.id): u'2',
            '{0}_radio_choices-MAX_NUM_FORMS'.format(self.radio_poll.id): u'1000',
            '{0}_radio_choices-0-id'.format(self.radio_poll.id): self.radio_poll_choice1.id,
            '{0}_radio_choices-0-answer'.format(self.radio_poll.id): u'Radio Poll - Answer 1',
            '{0}_radio_choices-0-DELETE'.format(self.radio_poll.id): False,
            '{0}_radio_choices-1-id'.format(self.radio_poll.id): self.radio_poll_choice2.id,
            '{0}_radio_choices-1-answer'.format(self.radio_poll.id): u'Radio Poll - Answer 2',
            '{0}_radio_choices-1-DELETE'.format(self.radio_poll.id): False}

        self.edit_current_data = {
            'name': u'Test edit voting',
            'description': u'This is a description.',
            'created_by': self.nominee1.id,
            'valid_groups': self.admin_group.id,
            'start_form_0_year': 2011,
            'end_form_0_year': now().year,
            'end_form_0_month': 10,
            'end_form_0_day': 4,
            'end_form_1_hour': 7,
            'end_form_1_minute': 00}

        # Give permissions to admin group
        group = Group.objects.get(name='Admin')
        permissions = Permission.objects.filter(name__icontains='poll')
        for perm in permissions:
            group.permissions.add(perm)

    def test_view_list_votings(self):
        """Get list votings page."""

        # Get as anonymous user.
        client = Client()
        response = client.get(reverse('voting_list_votings'), follow=True)
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'main.jinja')

        # Get as logged in Rep.
        with self.login(self.rep) as client:
            response = client.get(reverse('voting_list_votings'))
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'list_votings.jinja')

    @mock.patch('remo.voting.views.messages')
    def test_view_current_voting(self, faked_message):
        """View a voting."""
        rep_group = Group.objects.get(name='Rep')
        poll_start = now() - timedelta(days=5)
        poll = PollFactory.create(valid_groups=rep_group,
                                  end=poll_start + timedelta(days=10))

        # Anonymous user.
        c = Client()
        response = c.get(poll.get_absolute_url(), follow=True)
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'main.jinja')

        # Logged in user.
        with self.login(self.rep) as client:
            response = client.get(poll.get_absolute_url())
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'vote_voting.jinja')

        # # Logged in as a mozillian user - not valid voting group.
        with self.login(self.mozillian) as client:
            response = client.get(poll.get_absolute_url(), follow=True)
        faked_message.error.assert_called_once_with(
            mock.ANY, 'You do not have the permissions to vote on this voting.')
        self.assertJinja2TemplateUsed(response, 'list_votings.jinja')

    @mock.patch('remo.voting.views.messages')
    def test_view_cast_a_vote(self, fake_messages):
        """Cast a vote on a voting."""
        UserFactory.create(username='remobot')
        poll_start = now() - timedelta(days=5)
        poll = PollFactory.create(valid_groups=self.rep_group, start=poll_start,
                                  end=poll_start + timedelta(days=10),
                                  comments_allowed=False)

        # Cast a vote as a valid user.
        with self.login(self.rep) as client:
            response = client.post(poll.get_absolute_url(), self.post_data)
        self.assertJinja2TemplateUsed(response, 'list_votings.jinja')
        fake_messages.success.assert_called_once_with(
            mock.ANY, 'Your vote has been successfully registered.')

        # Ensure that there is a vote for user 'rep'
        poll = Poll.objects.get(id=poll.id)
        eq_(poll.users_voted.filter(username=self.rep.username).count(), 1)

        # Cast a vote as a valid user for a second time.
        with self.login(self.rep) as client:
            response = client.post(poll.get_absolute_url(), self.post_data, follow=True)
        self.assertJinja2TemplateUsed(response, 'list_votings.jinja')
        fake_messages.warning.assert_called_once_with(
            mock.ANY, ('You have already cast your vote for this voting. '
                       'Come back to see the results on %s UTC.'
                       % poll.end.strftime('%Y %B %d, %H:%M')))
        eq_(poll.users_voted.filter(username=self.rep.username).count(), 1)

        # Cast a vote as an invalid user.
        with self.login(self.mozillian) as client:
            response = client.post(poll.get_absolute_url(), self.post_data, follow=True)
        self.assertJinja2TemplateUsed(response, 'list_votings.jinja')
        fake_messages.error.assert_called_once_with(
            mock.ANY, ('You do not have the permissions to vote '
                       'on this voting.'))
        eq_(poll.users_voted.filter(username=self.mozillian.username).count(), 0)

    @mock.patch('remo.voting.views.messages')
    def test_view_post_a_comment(self, fake_messages):
        """Post a comment on an automated poll."""
        poll_start = now() - timedelta(days=5)
        poll_user = UserFactory.create(groups=['Council'])
        poll_group = Group.objects.get(name='Council')
        bug = BugFactory.create()
        swag_poll = PollFactory.create(name='swag poll', start=poll_start,
                                       end=poll_start + timedelta(days=15),
                                       created_by=poll_user,
                                       valid_groups=poll_group,
                                       bug=bug,
                                       automated_poll=True,
                                       description='Swag poll description.',
                                       slug='swag-poll')
        vote_url = reverse('voting_view_voting',
                           kwargs={'slug': 'swag-poll'})
        factory = RequestFactory()
        request = factory.post(vote_url, {'comment': 'This is a comment'},
                               follow=True)
        request.user = poll_user

        view_voting(request, slug=swag_poll.slug)
        poll_comment = PollComment.objects.get(poll=swag_poll)
        eq_(poll_comment.user, poll_user)
        eq_(poll_comment.comment, 'This is a comment')
        fake_messages.success.assert_called_once_with(
            mock.ANY, 'Comment saved successfully.')

    @mock.patch('remo.voting.views.messages')
    def test_view_voting_results(self, faked_message):
        """View the results of a voting."""
        poll_start = now() - timedelta(days=5)
        poll = PollFactory.create(valid_groups=self.rep_group,
                                  start=poll_start,
                                  end=poll_start - timedelta(days=3),
                                  comments_allowed=False)

        # Anonymous user.
        client = Client()
        response = client.get(poll.get_absolute_url(), follow=True)
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'main.jinja')

        # Logged in user.
        with self.login(self.rep) as client:
            response = client.get(poll.get_absolute_url())
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'view_voting.jinja')

        # Logged in user, invalid voting group.
        with self.login(self.mozillian) as client:
            response = client.get(poll.get_absolute_url())
        self.assertJinja2TemplateUsed(response, 'list_votings.jinja')
        faked_message.error.assert_called_once_with(
            mock.ANY, 'You do not have the permissions to vote on this voting.')

    def test_view_future_voting(self):
        """View a voting planned to start in the future."""
        poll_start = now() + timedelta(days=5)
        poll = PollFactory.create(valid_groups=self.rep_group,
                                  start=poll_start,
                                  end=poll_start + timedelta(days=10),
                                  comments_allowed=False)

        with self.login(self.rep) as client:
            response = client.get(poll.get_absolute_url())
        self.assertJinja2TemplateUsed(response, 'vote_voting.jinja')

    def test_view_edit_future_voting(self):
        """Edit future voting test."""

        # logged in as a non-admin user.
        with mock.patch('remo.base.decorators.messages.error') as faked_message:
            with self.login(self.rep) as client:
                response = client.post(reverse('voting_edit_voting',
                                               kwargs={'slug': self.poll.slug}),
                                       self.edit_future_data,
                                       follow=True)
            eq_(response.request['PATH_INFO'], '/')
            ok_(faked_message.called)
            eq_(faked_message.call_args_list[0][0][1], 'Permission denied.')

        # Logged in as administrator.
        with mock.patch('remo.voting.views.messages.success') as faked_message:
            with self.login(self.admin) as client:
                response = client.post(reverse('voting_edit_voting',
                                               kwargs={'slug': self.poll.slug}),
                                       self.edit_future_data)
            eq_(response.request['PATH_INFO'],
                reverse('voting_edit_voting', kwargs={'slug': self.poll.slug}))
            ok_(faked_message.called)
            eq_(faked_message.call_args_list[0][0][1], 'Voting successfully edited.')

        # Ensure voting data get saved.
        poll = Poll.objects.get(name='Test edit voting')

        # Test fields with the same name in POST data and models.
        excluded = ['valid_groups', 'created_by']
        for field in set(self.edit_future_data).difference(set(excluded)):
            if getattr(poll, field, None):
                eq_(getattr(poll, field), self.edit_future_data[field])

        # Test excluded fields.
        eq_(self.edit_future_data['valid_groups'], poll.valid_groups.id)
        eq_(self.edit_future_data['created_by'], poll.created_by.id)

        # Ensure Range/Radio Polls are saved.
        range_poll = RangePoll.objects.get(poll_id=poll.id)

        nominees = []
        for choice in RangePollChoice.objects.filter(range_poll_id=range_poll.id):
            nominees.append(choice.nominee.id)

        # Ensure that the nominees saved in the poll are the same with the POST data
        eq_(set([self.nominee1.id, self.nominee2.id, self.nominee3.id]), set(nominees))

        name = self.edit_future_data['range_polls-0-name']
        eq_(name, range_poll.name)

        radio_poll = RadioPoll.objects.get(poll_id=poll.id)

        answers = []
        for choice in RadioPollChoice.objects.filter(radio_poll_id=radio_poll.id):
            answers.append(choice.answer)
        eq_(set(['Radio Poll - Answer 1', 'Radio Poll - Answer 2']), set(answers))

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
        poll_start = now() - timedelta(days=5)
        poll = PollFactory.create(valid_groups=self.admin_group, start=poll_start,
                                  end=poll_start + timedelta(days=10),
                                  comments_allowed=False,
                                  created_by=self.nominee1)

        # Logged in as a non-admin user.
        with mock.patch('remo.base.decorators.messages.error') as faked_message:
            with self.login(self.rep) as client:
                response = client.post(reverse('voting_edit_voting', kwargs={'slug': poll.slug}),
                                       self.edit_current_data, follow=True)
            eq_(response.request['PATH_INFO'], '/')
            ok_(faked_message.called)
            eq_(faked_message.call_args_list[0][0][1], 'Permission denied.')

        # Logged in as administrator.
        with mock.patch('remo.voting.views.messages.success') as faked_message:
            with self.login(self.admin) as client:
                response = client.post(reverse('voting_edit_voting', kwargs={'slug': poll.slug}),
                                       self.edit_current_data, follow=True)
            eq_(response.request['PATH_INFO'],
                reverse('voting_edit_voting', kwargs={'slug': poll.slug}))
            ok_(faked_message.called)
            eq_(faked_message.call_args_list[0][0][1], 'Voting successfully edited.')

        # Ensure voting data get saved.
        poll = Poll.objects.get(name='Test edit voting')

        # Test fields with the same name in POST data and models.
        excluded = ['valid_groups', 'created_by']
        for field in set(self.edit_current_data).difference(set(excluded)):
            if getattr(poll, field, None):
                eq_(getattr(poll, field), self.edit_current_data[field])

        # Test excluded fields.
        eq_(self.edit_current_data['created_by'], poll.created_by.id)
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
        poll_start = now() - timedelta(days=5)
        poll = PollFactory.create(valid_groups=self.admin_group, start=poll_start,
                                  end=poll_start + timedelta(days=10),
                                  comments_allowed=False,
                                  created_by=self.nominee1)

        # Anonymous user
        c = Client()
        response = c.get(reverse('voting_edit_voting', kwargs={'slug': poll.slug}), follow=True)
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'main.jinja')

        # Logged in user.
        with mock.patch('remo.base.decorators.messages.error') as faked_message:
            with self.login(self.rep) as client:
                response = client.get(reverse('voting_edit_voting', kwargs={'slug': poll.slug}),
                                      follow=True)
            self.assertJinja2TemplateUsed(response, 'main.jinja')
            ok_(faked_message.called)
            eq_(faked_message.call_args_list[0][0][1], 'Permission denied.')

        # Logged in as admin
        with self.login(self.admin) as client:
            response = client.get(reverse('voting_edit_voting', kwargs={'slug': poll.slug}))
            self.assertJinja2TemplateUsed(response, 'edit_voting.jinja')

    def test_view_delete_voting(self):
        """Test delete voting."""

        # Anonymous user.
        with mock.patch('remo.base.decorators.messages.warning') as faked_message:
            c = Client()
            response = c.get(reverse('voting_delete_voting',
                                     kwargs={'slug': self.poll.slug}),
                             follow=True)
            self.assertJinja2TemplateUsed(response, 'main.jinja')
            ok_(faked_message.called)
            eq_(faked_message.call_args_list[0][0][1], 'Please login.')

        # Valid user with no permissions.
        with mock.patch('remo.base.decorators.messages.error') as faked_message:
            with self.login(self.rep) as client:
                response = client.get(reverse('voting_delete_voting',
                                              kwargs={'slug': self.poll.slug}),
                                      follow=True)
            self.assertJinja2TemplateUsed(response, 'main.jinja')
            ok_(faked_message.called)
            eq_(faked_message.call_args_list[0][0][1], 'Permission denied.')

        # Login as administrator.
        with mock.patch('remo.voting.views.messages.success') as faked_message:
            with self.login(self.admin) as client:
                response = client.post(reverse('voting_delete_voting',
                                               kwargs={'slug': self.poll.slug}),
                                       follow=True)
            self.assertJinja2TemplateUsed(response, 'list_votings.jinja')
            ok_(faked_message.called)
            eq_(faked_message.call_args_list[0][0][1], 'Voting successfully deleted.')

    def test_view_delete_automated_poll(self):
        with mute_signals(post_save):
            poll_start = now() - timedelta(days=5)
            poll_user = UserFactory.create(groups=['Review'])
            poll_group = Group.objects.get(name='Review')
            bug = BugFactory.create()
            swag_poll = PollFactory.create(name='swag poll', start=poll_start,
                                           end=poll_start + timedelta(days=15),
                                           created_by=poll_user,
                                           valid_groups=poll_group,
                                           bug=bug,
                                           automated_poll=True,
                                           description='Swag poll description.',
                                           slug='swag-poll')

        with mock.patch('remo.voting.views.messages.success') as faked_message:
            with self.login(self.admin) as client:
                response = client.post(reverse('voting_delete_voting',
                                               kwargs={'slug': swag_poll.slug}),
                                       follow=True)
            self.assertJinja2TemplateUsed(response, 'list_votings.jinja')
            ok_(faked_message.called)
            eq_(faked_message.call_args_list[0][0][1], 'Voting successfully deleted.')
            ok_(not Poll.objects.filter(id=swag_poll.id).exists())
            ok_(not Bug.objects.filter(id=bug.id).exists())


class VotingCommentingSystem(RemoTestCase):

    @mock.patch('remo.voting.views.messages.success')
    @mock.patch('remo.voting.views.forms.PollCommentForm')
    def test_post_a_comment(self, form_mock, messages_mock):
        user = UserFactory.create(groups=['Rep'])
        group = Group.objects.get(name='Rep')
        poll = PollFactory.create(created_by=user, valid_groups=group)
        form_mock.is_valid.return_value = True
        with self.login(user) as client:
            response = client.post(poll.get_absolute_url(),
                                   user=user,
                                   data={'comment': 'This is a comment'})
        eq_(response.status_code, 200)
        messages_mock.assert_called_with(
            mock.ANY, 'Comment saved successfully.')
        ok_(form_mock().save.called)
        eq_(response.context['poll'], poll)
        self.assertJinja2TemplateUsed(response, 'vote_voting.jinja')

    @mock.patch('remo.voting.views.redirect', wraps=redirect)
    def test_delete_as_owner(self, redirect_mock):
        user = UserFactory.create(groups=['Rep'])
        group = Group.objects.get(name='Rep')
        poll = PollFactory.create(created_by=user, valid_groups=group)
        comment = PollCommentFactory.create(poll=poll, user=user,
                                            comment='This is a comment')
        with self.login(user) as client:
            client.post(comment.get_absolute_delete_url(), user=comment.user)
        ok_(not PollComment.objects.filter(pk=comment.id).exists())
        redirect_mock.assert_called_with(poll.get_absolute_url())

    @requires_login()
    def test_delete_as_anonymous(self):
        comment = PollCommentFactory.create()
        client = Client()
        client.post(comment.get_absolute_delete_url(), data={})
        ok_(PollComment.objects.filter(pk=comment.id).exists())

    @requires_permission()
    def test_delete_as_other_rep(self):
        user = UserFactory.create(groups=['Rep'])
        group = Group.objects.get(name='Rep')
        poll = PollFactory.create(created_by=user, valid_groups=group)
        comment = PollCommentFactory.create(poll=poll, user=user,
                                            comment='This is a comment')
        other_rep = UserFactory.create(groups=['Rep'])
        with self.login(other_rep) as client:
            client.post(comment.get_absolute_delete_url(), user=other_rep)
        ok_(PollComment.objects.filter(pk=comment.id).exists())

    @mock.patch('remo.reports.views.redirect', wraps=redirect)
    def test_delete_as_admin(self, redirect_mock):
        user = UserFactory.create(groups=['Admin'])
        comment = PollCommentFactory.create()
        with self.login(user) as client:
            client.post(comment.get_absolute_delete_url(), user=user)
        ok_(not PollComment.objects.filter(pk=comment.id).exists())
