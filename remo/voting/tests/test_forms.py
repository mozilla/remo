import pytz
from datetime import datetime

from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory
from django.utils.timezone import now

from nose.tools import ok_

from remo.base.tests import RemoTestCase
from remo.profiles.tests import UserFactory
from remo.voting import forms
from remo.voting.models import Poll, RadioPoll, RangePoll
from remo.voting.tests import (PollFactory, RadioPollFactory,
                               RadioPollChoiceFactory, RangePollFactory,
                               RangePollChoiceFactory)


class PollAddFormTest(RemoTestCase):
    """Tests related to PollAddForm form."""

    def setUp(self):
        """Initial setup for the tests."""
        self.poll = PollFactory.create()
        self.radio_poll = RadioPollFactory.create(poll=self.poll)
        self.radio_poll_choice = (
            RadioPollChoiceFactory.create(radio_poll=self.radio_poll))
        self.range_poll = RangePollFactory.create(poll=self.poll)
        self.range_poll_choice = (
            RangePollChoiceFactory.create(range_poll=self.range_poll))
        UserFactory.create_batch(20, groups=['Rep'])
        self.user_list = (
            User.objects.filter(groups__name='Rep',
                                userprofile__registration_complete=True))
        self.user = self.user_list[0]

        self.form_data = {
            'description': u'This is a description.',
            'end_form_0_day': u'10',
            'end_form_0_month': u'2',
            'end_form_0_year': u'{0}'.format(now().year + 2),
            'end_form_1_hour': u'12',
            'end_form_1_minute': u'00',
            'name': u'Form data.',
            'start_form_0_day': u'10',
            'start_form_0_month': u'2',
            'start_form_0_year': u'{0}'.format(now().year + 1),
            'start_form_1_hour': u'12',
            'start_form_1_minute': u'00',
            'valid_groups': u'1'}

        self.radio_formset_data = {
            'radio_polls-0-id': u'%d' % self.radio_poll.id,
            'radio_polls-0-question': u'Radio Poll Example 2 - Question 1',
            'radio_polls-TOTAL_FORMS': u'1',
            'radio_polls-INITIAL_FORMS': u'1',
            'radio_polls-MAX_NUM_FORMS': u'1000',
            '%d_radio_choices-TOTAL_FORMS' % self.radio_poll.id: u'1',
            '%d_radio_choices-INITIAL_FORMS' % self.radio_poll.id: u'1',
            '%d_radio_choices-MAX_NUM_FORMS' % self.radio_poll.id: u'1000',
            '%d_radio_choices-0-id' % self.radio_poll.id: (
                u'%d' % self.radio_poll_choice.id),
            '%d_radio_choices-0-answer' % self.radio_poll.id: u'Answer 1',
            '%d_radio_choices-0-DELETE' % self.radio_poll.id: False}

        self.range_formset_data = {
            'range_polls-TOTAL_FORMS': u'1',
            'range_polls-INITIAL_FORMS': u'1',
            'range_polls-MAX_NUM_FORMS': u'1000',
            'range_polls-0-id': u'%d' % self.range_poll.id,
            'range_polls-0-name': u'Current Range Poll 1',
            '%d_range_choices-0-id' % self.range_poll.id: (
                u'%d' % self.range_poll.id),
            '%d_range_choices-0-nominee' % self.range_poll.id: (
                u'%d' % self.user.id),
            '%d_range_choices-0-DELETE' % self.range_poll.id: False,
            '%d_range_choices-TOTAL_FORMS' % self.range_poll.id: u'1',
            '%d_range_choices-INITIAL_FORMS' % self.range_poll.id: u'1',
            '%d_range_choices-MAX_NUM_FORMS' % self.range_poll.id: u'1000'}

        self.empty_radio_formset = {
            'radio_polls-TOTAL_FORMS': u'0',
            'radio_polls-INITIAL_FORMS': u'0',
            'radio_polls-MAX_NUM_FORMS': u'1000'}

        self.empty_range_formset = {
            'range_polls-TOTAL_FORMS': u'0',
            'range_polls-INITIAL_FORMS': u'0',
            'range_polls-MAX_NUM_FORMS': u'1000'}

        RangePollFormset = inlineformset_factory(Poll,
                                                 RangePoll,
                                                 formset=forms.BaseRangePollInlineFormSet,
                                                 extra=1,
                                                 exclude=('votes',),
                                                 can_delete=True)
        RadioPollFormset = inlineformset_factory(Poll,
                                                 RadioPoll,
                                                 formset=forms.BaseRadioPollInlineFormSet,
                                                 extra=1,
                                                 can_delete=True,
                                                 exclude=('votes',))

        self.range_poll_formset = RangePollFormset(self.range_formset_data,
                                                   instance=self.poll,
                                                   user_list=self.user_list)
        self.radio_poll_formset = RadioPollFormset(self.radio_formset_data, instance=self.poll)
        self.radio_poll_formset_empty = RadioPollFormset(self.empty_radio_formset,
                                                         instance=self.poll)
        self.range_poll_formset_empty = RangePollFormset(self.empty_range_formset,
                                                         instance=self.poll,
                                                         user_list=self.user_list)

    def test_clean_one_radio_one_range_poll(self):
        """Test with valid data for one radio and one range poll."""
        poll = PollFactory.create(start=datetime(now().year + 1, 2, 1, tzinfo=pytz.UTC))
        form = forms.PollAddForm(data=self.form_data,
                                 instance=poll,
                                 radio_poll_formset=self.radio_poll_formset,
                                 range_poll_formset=self.range_poll_formset)
        ok_(form.is_valid())

    def test_clean_one_radio_poll(self):
        """Test with valid data for one radio poll."""
        form = forms.PollAddForm(data=self.form_data,
                                 instance=self.poll,
                                 radio_poll_formset=self.radio_poll_formset,
                                 range_poll_formset=self.range_poll_formset_empty)
        ok_(form.is_valid())

    def test_clean_one_range_poll(self):
        """Test with valid data for one range poll."""
        form = forms.PollAddForm(data=self.form_data,
                                 instance=self.poll,
                                 radio_poll_formset=self.radio_poll_formset_empty,
                                 range_poll_formset=self.range_poll_formset)
        ok_(form.is_valid())

    def test_clean_without_radio_or_range_poll(self):
        """Test with empty data.

        If both radio_poll_formset and range_poll_formset are empty,
        then PollForm is invalid.

        """
        form = forms.PollAddForm(data=self.form_data,
                                 instance=self.poll,
                                 radio_poll_formset=self.radio_poll_formset_empty,
                                 range_poll_formset=self.range_poll_formset_empty)
        ok_(not form.is_valid())


class TestVoteForm(RemoTestCase):

    def test_base(self):
        poll = PollFactory.create()
        range_poll = RangePollFactory.create(poll=poll)
        RangePollChoiceFactory.create(range_poll=range_poll)
        data = {'range_poll__{0}'.format(range_poll.choices.all()[0].id): u'1'}
        vote_form = forms.RangePollChoiceVoteForm(data=data,
                                                  choices=range_poll.choices.all())
        ok_(vote_form.is_valid())

    def test_invalid(self):
        poll = PollFactory.create()
        range_poll = RangePollFactory.create(poll=poll)
        RangePollChoiceFactory.create(range_poll=range_poll)
        field_name = 'range_poll__{0}'.format(range_poll.choices.all()[0].id)
        data = {field_name: u'0'}
        vote_form = forms.RangePollChoiceVoteForm(data=data,
                                                  choices=range_poll.choices.all())
        ok_(not vote_form.is_valid())
        ok_(field_name in vote_form.errors)
        ok_(vote_form[field_name], 'You must vote at least one nominee')
