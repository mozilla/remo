import happyforms
import pytz
from datetime import datetime

from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import F
from django.forms.models import BaseInlineFormSet, inlineformset_factory
from django.utils.timezone import make_naive, utc

from datetimewidgets import SplitSelectDateTimeWidget
from remo.base.utils import datetime2pdt, validate_datetime
from models import Poll, RadioPoll, RadioPollChoice, RangePoll, RangePollChoice


class RangePollChoiceVoteForm(happyforms.Form):
    """Range voting vote form."""
    def __init__(self, choices, *args, **kwargs):
        """Initialize form

        Dynamically set fields for the participants in a range voting.
        """
        super(RangePollChoiceVoteForm, self).__init__(*args, **kwargs)
        nominees = [(i, '%d' % i) for i in range(0, choices.count()+1)]
        for choice in choices:
            self.fields['range_poll__%s' % str(choice.id)] = (
                forms.ChoiceField(widget=forms.Select(),
                                  choices=nominees,
                                  label=choice.nominee.get_full_name()))

    def save(self, *args, **kwargs):
        for nominee_id, votes in self.cleaned_data.items():
            nominee_id = nominee_id.split('__')[1]
            (RangePollChoice.objects
             .filter(pk=nominee_id).update(votes=F('votes')+int(votes)))


class RadioPollChoiceVoteForm(happyforms.Form):
    """Radio voting vote form."""
    def __init__(self, radio_poll, *args, **kwargs):
        """Initialize form

        Dynamically set field for the answers in a radio voting.
        """
        super(RadioPollChoiceVoteForm, self).__init__(*args, **kwargs)
        choices = (((None, '----'),) +
                   tuple(radio_poll.answers.values_list('id', 'answer')))
        self.fields['radio_poll__%s' % str(radio_poll.id)] = (
            forms.ChoiceField(widget=forms.Select(),
                              choices=choices,
                              label=radio_poll.question))

    def save(self, *args, **kwargs):
        answer_id = self.cleaned_data.values()[0]
        if answer_id != 'None':
            (RadioPollChoice.objects
             .filter(pk=answer_id).update(votes=F('votes')+1))


class PollEditForm(happyforms.ModelForm):
    """Poll Edit Form."""
    name = forms.CharField(required=True)
    end = forms.DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        """Initialize form.

        Dynamically set some fields of the form.
        """
        super(PollEditForm, self).__init__(*args, **kwargs)

        instance = self.instance
        # Set the year portion of the widget
        now = datetime.utcnow()
        end_year = min(getattr(self.instance.end, 'year', now.year),
                       now.year - 1)
        self.fields['end_form'] = forms.DateTimeField(
            widget=SplitSelectDateTimeWidget(
                years=range(end_year, now.year + 10), minute_step=5),
            validators=[validate_datetime])
        if self.instance.end:
            # Convert to server timezone
            naive_time = make_naive(instance.end, pytz.UTC)
            server_time = datetime2pdt(naive_time)
            self.fields['end_form'].initial = server_time

    def clean(self):
        """Clean form."""
        super(PollEditForm, self).clean()

        cdata = self.cleaned_data
        date_now = datetime2pdt()

        # Check if key exists
        if not 'end_form' in cdata:
            raise ValidationError('Please correct the form errors.')

        cdata['end'] = cdata['end_form'].replace(tzinfo=utc)

        if cdata['end'] < date_now:
            msg = 'End date should not be in the past.'
            self._errors['end_form'] = self.error_class([msg])

        return cdata

    class Meta:
        model = Poll
        fields = ['name', 'end', 'description']
        widgets = {'end': SplitSelectDateTimeWidget()}


class PollAddForm(PollEditForm):
    """Poll Add Form."""
    start = forms.DateTimeField(required=False)
    valid_groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        error_messages={'required': 'Please select an option from the list.'})

    def __init__(self, *args, **kwargs):
        """Initialize form.

        Dynamically set some fields of the form.
        """
        self.range_poll_formset = kwargs.pop('range_poll_formset')
        self.radio_poll_formset = kwargs.pop('radio_poll_formset')
        super(PollAddForm, self).__init__(*args, **kwargs)

        instance = self.instance
        # Set the year portion of the widget
        now = datetime.utcnow()
        start_year = min(getattr(self.instance.start, 'year', now.year),
                         now.year - 1)
        self.fields['start_form'] = forms.DateTimeField(
            widget=SplitSelectDateTimeWidget(
                years=range(start_year, now.year + 10), minute_step=5),
            validators=[validate_datetime])

        if self.instance.start:
            naive_time = make_naive(instance.start, pytz.UTC)
            server_time = datetime2pdt(naive_time)
            self.fields['start_form'].initial = server_time

    def is_valid(self):
        """Override the is_valid() method."""
        return (super(PollAddForm, self).is_valid()
                and (self.range_poll_formset.is_valid()
                     and self.radio_poll_formset.is_valid()))

    def clean(self):
        """Clean form."""
        super(PollAddForm, self).clean()

        cdata = self.cleaned_data
        date_now = datetime2pdt()

        # Check if key exists
        if not 'start_form' in cdata:
            raise ValidationError('Please correct the form errors.')

        cdata['start'] = cdata['start_form'].replace(tzinfo=utc)

        if cdata['start_form'] >= cdata['end_form']:
            msg = 'Start date should come before end date.'
            self._errors['start_form'] = self.error_class([msg])
        if cdata['start'] < date_now:
            msg = 'Start date should not be in the past.'
            self._errors['start_form'] = self.error_class([msg])

        # Check that there is at least one radio or range poll
        if ((not self.range_poll_formset._count_filled_forms()) and
                (not self.radio_poll_formset._count_filled_forms())):
            msg = u'You must fill at least one radio or range poll.'
            raise ValidationError(msg)

        return cdata

    def save(self, commit=True):
        """Override save method."""
        super(PollAddForm, self).save()
        self.radio_poll_formset.save_all()
        self.range_poll_formset.save_all()

    class Meta:
        model = Poll
        fields = ['name', 'start', 'end', 'valid_groups', 'description']
        widgets = {'start': SplitSelectDateTimeWidget(),
                   'end': SplitSelectDateTimeWidget()}


class BaseRangePollChoiceInlineFormset(BaseInlineFormSet):
    _user_list = None

    def __init__(self, *args, **kwargs):
        """Initialize form."""
        self._user_list = kwargs.pop('user_list')
        (super(BaseRangePollChoiceInlineFormset, self)
         .__init__(*args, **kwargs))

    def add_fields(self, form, index):
        """Add extra fields."""
        super(BaseRangePollChoiceInlineFormset, self).add_fields(form, index)
        form.fields['nominee'].queryset = self._user_list

    def clean(self):
        """Clean form.

        Check if the user has already been nominated in
        the same voting.
        """
        if any(self.errors):
            # Do not check, unless all forms are valid
            return
        names = []
        for i, form in enumerate(self.forms):
            if 'nominee' in form.cleaned_data:
                name = form.cleaned_data['nominee']
                if name in names:
                    self.errors[i]['nominee'] = (u'This user has already '
                                                 'been nominated.')
                    raise ValidationError({'nominee': ['Error']})
                names.append(name)

    class Meta:
        model = RangePollChoice


RangePollChoiceFormset = (inlineformset_factory(RangePoll, RangePollChoice,
                          formset=BaseRangePollChoiceInlineFormset, extra=1,
                          exclude='votes', can_delete=True))


class BaseRangePollInlineFormSet(BaseInlineFormSet):
    """Formset for range polls."""
    def __init__(self, *args, **kwargs):
        self._user_list = kwargs.pop('user_list')
        """Init with minimum number of 1 form."""
        super(BaseRangePollInlineFormSet, self).__init__(*args, **kwargs)

    def _count_filled_forms(self):
        """Count valid, filled forms with delete == False."""
        return len([form for form in self.forms if
                    form.is_valid() and
                    len(form.cleaned_data) and
                    form.cleaned_data['DELETE'] is False])

    def add_fields(self, form, index):
        """Add extra fields."""
        super(BaseRangePollInlineFormSet, self).add_fields(form, index)
        # create the nested formset
        try:
            instance = self.get_queryset()[index]
            pk_value = instance.pk
        except IndexError:
            instance = None
            pk_value = form.prefix

        data = self.data if self.data and index is not None else None

        # store the formset in the .nested property
        form.nested = [
            RangePollChoiceFormset(data=data, instance=instance,
                                   prefix='%s_range_choices' % pk_value,
                                   user_list=self._user_list)]

    def is_valid(self):
        """Validate nested forms."""
        result = super(BaseRangePollInlineFormSet, self).is_valid()

        for form in self.forms:
            if hasattr(form, 'nested'):
                for n in form.nested:
                    if form.is_bound:
                        n.is_bound = True
                    for nform in n:
                        nform.data = form.data
                        if form.is_bound:
                            nform.is_bound = True
                    result = result and n.is_valid()
        return result

    def save_new(self, form, commit=True):
        """Override save_new to save new data.

        Saves and returns a new model instance for the given form.
        """
        instance = (super(BaseRangePollInlineFormSet, self)
                    .save_new(form, commit=commit))

        # Updated form's instance ref
        form.instance = instance

        # Do the same for nested forms
        for nested in form.nested:
            nested.instance = instance

        # Go over cleaned data
        for cd in nested.cleaned_data:
            cd[nested.fk.name] = instance

        return instance

    def save_all(self, commit=True):
        """Save objects on all nested forms."""
        objects = self.save(commit=False)

        if commit:
            for o in objects:
                o.save()

        for form in set(self.initial_forms + self.saved_forms):
            for nested in form.nested:
                nested.save(commit=commit)

    def clean(self):
        """Clean form.

        Check that each Poll has a unique name.
        """
        if any(self.errors):
            # Do not check, unless all forms are valid
            return
        names = []
        for i, form in enumerate(self.forms):
            if 'name' in form.cleaned_data:
                name = form.cleaned_data['name']
                if name in names:
                    self.errors[i]['name'] = (u'Each range poll '
                                              'must have a unique name')
                    raise ValidationError({'name': ['Error']})
                names.append(name)

        return super(BaseRangePollInlineFormSet, self).clean()


class BaseRadioPollChoiceInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        """Initialize form."""
        (super(BaseRadioPollChoiceInlineFormset, self)
         .__init__(*args, **kwargs))

    def clean(self):
        """Clean form.

        Check if the same answer has already been submited
        in the same voting.
        """
        if any(self.errors):
            # Do not check, unless all forms are valid
            return
        answers = []
        for i, form in enumerate(self.forms):
            if 'answer' in form.cleaned_data:
                answer = form.cleaned_data['answer']
                if answer in answers:
                    self.errors[i]['answer'] = (u'This answer has already '
                                                'been submited.')
                    raise ValidationError({'answer': ['Error']})
                answers.append(answer)

    class Meta:
        model = RadioPollChoice


RadioPollChoiceFormset = (inlineformset_factory(RadioPoll, RadioPollChoice,
                          formset=BaseRadioPollChoiceInlineFormset, extra=1,
                          exclude='votes', can_delete=True))


class BaseRadioPollInlineFormSet(BaseInlineFormSet):
    """Formset for range polls."""
    def __init__(self, *args, **kwargs):
        """Initialize form."""
        super(BaseRadioPollInlineFormSet, self).__init__(*args, **kwargs)

    def _count_filled_forms(self):
        """Count valid, filled forms with delete == False."""
        return len([form for form in self.forms if
                    form.is_valid() and
                    len(form.cleaned_data) and
                    form.cleaned_data['DELETE'] is False])

    def add_fields(self, form, index):
        """Add extra fields."""
        super(BaseRadioPollInlineFormSet, self).add_fields(form, index)
        # create the nested formset
        try:
            instance = self.get_queryset()[index]
            pk_value = instance.pk
        except IndexError:
            instance = None
            pk_value = form.prefix

        data = self.data if self.data and index is not None else None
        # store the formset in the .nested property
        form.nested = [
            RadioPollChoiceFormset(data=data, instance=instance,
                                   prefix='%s_radio_choices' % pk_value)]

    def is_valid(self):
        """Validate nested forms."""
        result = super(BaseRadioPollInlineFormSet, self).is_valid()

        for form in self.forms:
            if hasattr(form, 'nested'):

                for n in form.nested:
                    n.data = form.data
                    if form.is_bound:
                        n.is_bound = True
                    for nform in n:
                        nform.data = form.data
                        if form.is_bound:
                            nform.is_bound = True
                    result = result and n.is_valid()

        return result

    def save_new(self, form, commit=True):
        """Override save_new to save new data.

        Saves and returns a new model instance for the given form
        """
        instance = (super(BaseRadioPollInlineFormSet, self)
                    .save_new(form, commit=commit))

        # Updated form's instance ref
        form.instance = instance

        # Do the same for nested forms
        for nested in form.nested:
            nested.instance = instance

        # Go over cleaned data
        for cd in nested.cleaned_data:
            cd[nested.fk.name] = instance

        return instance

    def save_all(self, commit=True):
        """Save objects on all nested forms."""
        objects = self.save(commit=False)

        if commit:
            for o in objects:
                o.save()

        for form in set(self.initial_forms + self.saved_forms):
            for nested in form.nested:
                nested.save(commit=commit)

    def clean(self):
        """Clean form.

        Check that each Radio Poll has a unique name.
        """
        if any(self.errors):
            # Do not check, unless all forms are valid
            return
        questions = []
        for i, form in enumerate(self.forms):
            if 'question' in form.cleaned_data:
                question = form.cleaned_data['question']
                if question in questions:
                    self.errors[i]['question'] = (u'Each question must be '
                                                  'unique in a radio poll')
                    raise ValidationError({'question': ['Error']})
                questions.append(question)

        return super(BaseRadioPollInlineFormSet, self).clean()
