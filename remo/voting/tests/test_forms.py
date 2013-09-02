from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory

from nose.tools import ok_
from test_utils import TestCase

from remo.profiles.tests import UserFactory
from remo.voting import forms
from remo.voting.models import Poll, RadioPoll, RangePoll
from remo.voting.tests import (PollFactory, RadioPollFactory,
                               RadioPollChoiceFactory, RangePollFactory,
                               RangePollChoiceFactory)


class PollAddFormTest(TestCase):
    """Tests related to PollAddForm form."""

    def setUp(self):
        """Initial setup for the tests."""
        self.poll = PollFactory.create()
        self.radio_poll = RadioPollFactory.create(poll=self.poll)
        self.radio_poll_choice = (RadioPollChoiceFactory
                                  .create(radio_poll=self.radio_poll))
        self.range_poll = RangePollFactory.create(poll=self.poll)
        self.range_poll_choice = (RangePollChoiceFactory
                                  .create(range_poll=self.range_poll))
        UserFactory.create_batch(20, groups=['Rep'])
        self._user_list = User.objects.filter(
            groups__name='Rep', userprofile__registration_complete=True)
        self._user = self._user_list[0]

        self.form_data = {
            'description': u'This is a description.',
            'end_form_0_day': u'1',
            'end_form_0_month': u'1',
            'end_form_0_year': u'2019',
            'end_form_1_hour': u'12',
            'end_form_1_minute': u'00',
            'name': u'Form data.',
            'start_form_0_day': u'1',
            'start_form_0_month': u'1',
            'start_form_0_year': u'2018',
            'start_form_1_hour': u'12',
            'start_form_1_minute': u'00',
            'valid_groups': u'1'}

        self.radio_formset_data = {
            'radio_polls-0-id': u'%s' % str(self.radio_poll.id),
            'radio_polls-0-question': u'Radio Poll Example 2 - Question 1',
            'radio_polls-TOTAL_FORMS': u'1',
            'radio_polls-INITIAL_FORMS': u'1',
            'radio_polls-MAX_NUM_FORMS': u'1000',
            '%s_radio_choices-TOTAL_FORMS' % str(self.radio_poll.id): u'1',
            '%s_radio_choices-INITIAL_FORMS' % str(self.radio_poll.id): u'1',
            '%s_radio_choices-MAX_NUM_FORMS' % str(self.radio_poll.id):
            u'1000',
            '%s_radio_choices-0-id' % str(self.radio_poll.id):
            u'%s' % str(self.radio_poll.id),
            '%s_radio_choices-0-answer' % str(self.radio_poll.id): u'Answer 1',
            '%s_radio_choices-0-DELETE' % str(self.radio_poll.id): False}

        self.range_formset_data = {
            'range_polls-TOTAL_FORMS': u'1',
            'range_polls-INITIAL_FORMS': u'1',
            'range_polls-MAX_NUM_FORMS': u'1000',
            'range_polls-0-id': u'%s' % str(self.range_poll.id),
            'range_polls-0-name': u'Current Range Poll 1',
            '%s_range_choices-0-id' % str(self.range_poll.id):
            u'%s' % str(self.range_poll.id),
            '%s_range_choices-0-nominee' % str(self.range_poll.id):
            u'%s' % str(self._user.id),
            '%s_range_choices-0-DELETE' % str(self.range_poll.id): False,
            '%s_range_choices-TOTAL_FORMS' % str(self.range_poll.id): u'1',
            '%s_range_choices-INITIAL_FORMS' % str(self.range_poll.id): u'1',
            '%s_range_choices-MAX_NUM_FORMS' % (
                str(self.range_poll.id)): u'1000'}

        self.empty_radio_formset = {
            'radio_polls-TOTAL_FORMS': u'0',
            'radio_polls-INITIAL_FORMS': u'0',
            'radio_polls-MAX_NUM_FORMS': u'1000'}

        self.empty_range_formset = {
            'range_polls-TOTAL_FORMS': u'0',
            'range_polls-INITIAL_FORMS': u'0',
            'range_polls-MAX_NUM_FORMS': u'1000'}

        RangePollFormset = (inlineformset_factory(Poll, RangePoll,
                            formset=forms.BaseRangePollInlineFormSet,
                            extra=1, can_delete=True))
        RadioPollFormset = (inlineformset_factory(Poll, RadioPoll,
                            formset=forms.BaseRadioPollInlineFormSet,
                            extra=1, can_delete=True))
        self.range_poll_formset = RangePollFormset(self.range_formset_data,
                                                   instance=self.poll,
                                                   user_list=self._user_list)
        self.radio_poll_formset = RadioPollFormset(self.radio_formset_data,
                                                   instance=self.poll)
        self.radio_poll_formset_invalid = RadioPollFormset(
            self.empty_radio_formset, instance=self.poll)
        self.range_poll_formset_invalid = RangePollFormset(
            self.empty_range_formset, instance=self.poll,
            user_list=self._user_list)

    def test_clean_one_radio_one_range_poll(self):
        """Test with valid data for one radio and one range poll."""
        form = forms.PollAddForm(data=self.form_data,
                                 instance=self.poll,
                                 radio_poll_formset=self.radio_poll_formset,
                                 range_poll_formset=self.range_poll_formset)
        ok_(form.is_valid())

    def test_clean_one_radio_poll(self):
        """Test with valid data for one radio poll."""
        form = forms.PollAddForm(data=self.form_data,
                                 instance=self.poll,
                                 radio_poll_formset=self.radio_poll_formset,
                                 range_poll_formset=(
                                     self.range_poll_formset_invalid))
        ok_(form.is_valid())

    def test_clean_one_range_poll(self):
        """Test with valid data for one range poll."""
        form = forms.PollAddForm(data=self.form_data,
                                 instance=self.poll,
                                 radio_poll_formset=(
                                     self.radio_poll_formset_invalid),
                                 range_poll_formset=self.range_poll_formset)
        ok_(form.is_valid())

    def test_clean_without_radio_or_range_poll(self):
        """Test with invalid data."""
        form = forms.PollAddForm(data=self.form_data,
                                 instance=self.poll,
                                 radio_poll_formset=(
                                     self.radio_poll_formset_invalid),
                                 range_poll_formset=(
                                     self.range_poll_formset_invalid))
        ok_(not form.is_valid())
