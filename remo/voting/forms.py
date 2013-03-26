from datetime import datetime

from happyforms import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.forms.formsets import DELETION_FIELD_NAME
from django.forms.models import BaseInlineFormSet, inlineformset_factory

from datetimewidgets import SplitSelectDateTimeWidget
from remo.base.utils import validate_datetime
from models import Poll, PollRange, PollRangeVotes, PollRadio, PollChoices


class PollForm(forms.ModelForm):
    """Form of a Poll."""
    name = forms.CharField(required=True)
    start = forms.DateTimeField(required=False)
    end = forms.DateTimeField(required=False)

    valid_groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        error_messages={'required': 'Please select an option from the list.'})

    def __init__(self, *args, **kwargs):
        """Initialize form.

        Dynamically set some fields of the form.
        """
        super(PollForm, self).__init__(*args, **kwargs)
        # Set the year portion of the widget
        now = datetime.now()
        start_year = getattr(self.instance.start, 'year', now.year)
        end_year = getattr(self.instance.end, 'year', now.year)
        self.fields['start_form'] = forms.DateTimeField(
            widget=SplitSelectDateTimeWidget(
                years=range(start_year, now.year + 10), minute_step=5),
            validators=[validate_datetime])
        self.fields['end_form'] = forms.DateTimeField(
            widget=SplitSelectDateTimeWidget(
                years=range(end_year, now.year + 10), minute_step=5),
            validators=[validate_datetime])
        if self.instance.start:
            self.fields['start_form'].initial = self.start
        if self.instance.end:
            self.fields['end_form'].initial = self.end

    def clean(self):
        """Clean form."""
        super(PollForm, self).clean()

        cdata = self.cleaned_data

        # Check if key exists
        if not ('start_form' or 'end_form') in cdata:
            raise ValidationError('Please correct the form errors.')

        cdata['start'] = cdata['start_form']
        cdata['end'] = cdata['end_form']

        # Directly write to self.errors as
        # ValidationError({'start_form': ['Error message']}) doesn't
        # seem to work.
        if cdata['start_form'] >= cdata['end_form']:
            self.errors['start_form'] = (u'Start date should come '
                                         'before end date.')
            raise ValidationError({'start_form': ['Error']})

        return cdata

    class Meta:
        model = Poll
        fields = ['name', 'start', 'end', 'valid_groups', 'description']
        widgets = {'start': SplitSelectDateTimeWidget(),
                   'end': SplitSelectDateTimeWidget()}


class BasePollRangeVotesInilineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        """Initialize form."""
        super(BasePollRangeVotesInilineFormset, self).__init__(*args, **kwargs)

    class Meta:
        model = PollRangeVotes


PollRangeVotesFormset = inlineformset_factory(
    PollRange, PollRangeVotes, formset=BasePollRangeVotesInilineFormset,
    extra=1, exclude='votes', can_delete=True)


class BasePollRangeInlineFormSet(BaseInlineFormSet):
    """Formset for poll ranges."""
    def __init__(self, *args, **kwargs):
        '''Init with minimum number of 1 form.'''
        super(BasePollRangeInlineFormSet, self).__init__(*args, **kwargs)

    def add_fields(self, form, index):
        super(BasePollRangeInlineFormSet, self).add_fields(form, index)
        # create the nested formset
        try:
            instance = self.get_queryset()[index]
            pk_value = instance.pk
        except IndexError:
            instance = None
            pk_value = hash(form.prefix)

        data = self.data if self.data and index is not None else None
        # store the formset in the .nested property
        form.nested = [PollRangeVotesFormset(
            data=data, instance=instance,
            prefix='RANGE_VOTES_%s' % pk_value)]

    def is_valid(self):
        result = super(BasePollRangeInlineFormSet, self).is_valid()

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
        Saves and returns a new model instance for the given form
        """

        instance = (super(BasePollRangeInlineFormSet, self)
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

    def _should_delete(self, form):
        """Check if the form's object will be deleted."""
        if self.can_delete:
            raw_delete_value = form._raw_value(DELETION_FIELD_NAME)
            should_delete = form.fields[DELETION_FIELD_NAME].clean(
                raw_delete_value)
            return should_delete
        return False

    def save_all(self, commit=True):
        objects = self.save(commit=False)

        if commit:
            for o in objects:
                o.save()

        if not commit:
            self.save_m2m()

        for form in set(self.initial_forms + self.saved_forms):
            if self._should_delete(form):
                continue
            for nested in form.nested:
                nested.save(commit=commit)

    def clean(self):
        if any(self.errors):
            # Do not check, unless all forms are valid
            return
        names = []
        '''Check that each Poll has a unique name.'''
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if 'name' in form.cleaned_data:
                name = form.cleaned_data['name']
                if name in names:
                    raise ValidationError('Name in a poll must be unique')
                names.append(name)

        return super(BasePollRangeInlineFormSet, self).clean()


PollRangeFormset = inlineformset_factory(
    Poll, PollRange, formset=BasePollRangeInlineFormSet,
    extra=1, can_delete=True)


#Poll Radio Voting section
class BasePollChoicesInilineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        """Initialize form."""
        super(BasePollChoicesInilineFormset, self).__init__(*args, **kwargs)

    class Meta:
        model = PollChoices


PollChoicesFormset = inlineformset_factory(
    PollRadio, PollChoices, formset=BasePollChoicesInilineFormset,
    extra=1, exclude='votes', can_delete=True)


class BasePollRadioInlineFormSet(BaseInlineFormSet):
    """Formset for poll ranges."""
    def __init__(self, *args, **kwargs):
        """Initialize form."""
        super(BasePollRadioInlineFormSet, self).__init__(*args, **kwargs)

    def add_fields(self, form, index):
        super(BasePollRadioInlineFormSet, self).add_fields(form, index)
        # create the nested formset
        try:
            instance = self.get_queryset()[index]
            pk_value = instance.pk
        except IndexError:
            instance = None
            pk_value = hash(form.prefix)

        data = self.data if self.data and index is not None else None
        # store the formset in the .nested property
        form.nested = [PollChoicesFormset(
            data=data, instance=instance,
            prefix='RADIO_CHOICES_%s' % pk_value)]

    def is_valid(self):
        result = super(BasePollRadioInlineFormSet, self).is_valid()

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

        instance = (super(BasePollRadioInlineFormSet, self)
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

    def _should_delete(self, form):
        """Check if the form's object will be deleted."""
        if self.can_delete:
            raw_delete_value = form._raw_value(DELETION_FIELD_NAME)
            should_delete = form.fields[DELETION_FIELD_NAME].clean(
                raw_delete_value)
            return should_delete
        return False

    def save_all(self, commit=True):
        objects = self.save(commit=False)

        if commit:
            for o in objects:
                o.save()

        if not commit:
            self.save_m2m()

        for form in set(self.initial_forms + self.saved_forms):
            if self._should_delete(form):
                continue
            for nested in form.nested:
                nested.save(commit=commit)

    def clean(self):
        if any(self.errors):
            # Do not check, unless all forms are valid
            return
        names = []
        '''Check that each Poll has a unique name.'''
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if 'name' in form.cleaned_data:
                name = form.cleaned_data['name']
                if name in names:
                    raise ValidationError('Name in a poll must be unique')
                names.append(name)

        return super(BasePollRadioInlineFormSet, self).clean()


PollRadioFormset = inlineformset_factory(
    Poll, PollRadio, formset=BasePollRadioInlineFormSet,
    extra=1, can_delete=True)
