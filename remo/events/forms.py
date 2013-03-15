from datetime import datetime
from happyforms import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.timezone import make_naive
from product_details import product_details

from pytz import common_timezones, timezone

from datetimewidgets import SplitSelectDateTimeWidget
from remo.base.helpers import get_full_name
from remo.base.utils import validate_datetime
from remo.remozilla.models import Bug

from models import Event, Metric

EST_ATTENDANCE_CHOICES = (('', 'Estimated attendance'),
                          (10, '1-10'),
                          (50, '11-50'),
                          (100, '51-100'),
                          (500, '101-500'),
                          (1000, '501-1000'),
                          (2000, '1000+'))


class MinBaseInlineFormSet(forms.models.BaseInlineFormSet):
    """Inline form-set support for minimum number of filled forms."""

    def __init__(self, *args, **kwargs):
        """Init formset with minimum number of 2 forms."""
        self.min_forms = kwargs.get('min_forms', 2)
        super(MinBaseInlineFormSet, self).__init__(*args, **kwargs)

    def _count_filled_forms(self):
        """Count valid, filled forms, with delete == False."""
        valid_forms = 0

        for form in self.forms:
            if (form.is_valid() and len(form.cleaned_data)):
                if form.cleaned_data['DELETE'] is False:
                    valid_forms += 1

        return valid_forms

    def clean(self):
        """Make sure that we have at least min_forms filled."""
        if (self.min_forms > self._count_filled_forms()):
            raise ValidationError('You must fill at least %d forms' %
                                  self.min_forms)

        return super(MinBaseInlineFormSet, self).clean()


EventMetricsFormset = forms.models.inlineformset_factory(
    Event, Metric, formset=MinBaseInlineFormSet, extra=2)


class EventForm(forms.ModelForm):
    """Form of an event."""
    country = forms.ChoiceField(
        choices=[],
        error_messages={'required': 'Please select one option from the list.'})
    swag_bug_form = forms.CharField(required=False)
    budget_bug_form = forms.CharField(required=False)
    estimated_attendance = forms.ChoiceField(
        choices=EST_ATTENDANCE_CHOICES,
        error_messages={'required': 'Please select one option from the list.'})
    owner = forms.IntegerField(required=False)
    timezone = forms.ChoiceField(choices=zip(common_timezones,
                                             common_timezones))
    start = forms.DateTimeField(required=False)
    end = forms.DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        """Initialize form.

        Dynamically set choices for country field.
        """
        if 'editable_owner' in kwargs:
            self.editable_owner = kwargs['editable_owner']
            del(kwargs['editable_owner'])

        super(EventForm, self).__init__(*args, **kwargs)

        # Dynamic countries field.
        countries = product_details.get_regions('en').values()
        countries.sort()
        country_choices = ([('', "Country")] +
                           [(country, country) for country in countries])
        self.fields['country'].choices = country_choices

        # Dynamic owner field.
        if self.editable_owner:
            self.fields['owner_form'] = forms.ModelChoiceField(
                queryset=User.objects.filter(
                    userprofile__registration_complete=True,
                    groups__name='Rep'),
                empty_label='Owner', initial=self.instance.owner.pk)
        else:
            self.fields['owner_form'] = forms.CharField(
                required=False, initial=get_full_name(self.instance.owner),
                widget=forms.TextInput(attrs={'readonly': 'readonly',
                                              'class': 'input-text big'}))

        instance = self.instance
        # Dynamically set the year portion of the datetime widget
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
        # Make times local to venue
        if self.instance.start:
            start = make_naive(instance.local_start,
                               timezone(instance.timezone))
            self.fields['start_form'].initial = start

        if self.instance.end:
            end = make_naive(instance.local_end, timezone(instance.timezone))
            self.fields['end_form'].initial = end

        # Use of intermediate fields to translate between bug.id and
        # bug.bug_id
        if instance.budget_bug:
            self.fields['budget_bug_form'].initial = instance.budget_bug.bug_id
        if instance.swag_bug:
            self.fields['swag_bug_form'].initial = instance.swag_bug.bug_id

    def clean(self):
        """Clean form."""
        super(EventForm, self).clean()

        cdata = self.cleaned_data

        cdata['budget_bug'] = cdata.get('budget_bug_form', None)
        cdata['swag_bug'] = cdata.get('swag_bug_form', None)
        if self.editable_owner:
            cdata['owner'] = cdata.get('owner_form', None)
        else:
            cdata['owner'] = self.instance.owner

        # Check if keys exists in cleaned data.
        if (not self.cleaned_data.has_key('start_form') or
                not self.cleaned_data.has_key('end_form')):
                raise ValidationError('Please correct the form errors.')
        # Set timezone
        t = timezone(cdata['timezone'])
        start = make_naive(cdata['start_form'],
                           timezone(settings.TIME_ZONE))
        cdata['start'] = t.localize(start)
        end = make_naive(cdata['end_form'],
                         timezone(settings.TIME_ZONE))
        cdata['end'] = t.localize(end)

        # Directly write to self.errors as
        # ValidationError({'start_form': ['Error message']}) doesn't
        # seem to work.
        if cdata['start'] >= cdata['end']:
            self.errors['start_form'] = (u'Start date should come '
                                         'before end date.')
            raise ValidationError({'start_form': ['Error']})

        return cdata

    def _clean_bug(self, bug_id, component):
        """Get or create Bug with bug_id and component. """
        if bug_id == '':
            return None

        try:
            bug_id = int(bug_id)
        except ValueError:
            raise ValidationError('Please provide a number')

        bug, created = Bug.objects.get_or_create(bug_id=bug_id,
                                                 component=component)

        return bug

    def clean_swag_bug_form(self):
        """Clean swag_bug_form field."""
        data = self.cleaned_data['swag_bug_form']
        return self._clean_bug(data, 'Swag Requests')

    def clean_budget_bug_form(self):
        """Clean budget_bug_form field."""
        data = self.cleaned_data['budget_bug_form']
        return self._clean_bug(data, 'Budget Requests')

    class Meta:
        model = Event
        fields = ['name', 'start', 'end', 'venue', 'region', 'owner',
                  'country', 'city', 'lat', 'lon', 'external_link',
                  'planning_pad_url', 'timezone', 'estimated_attendance',
                  'description', 'extra_content', 'hashtag', 'mozilla_event',
                  'swag_bug', 'budget_bug']
        widgets = {'lat': forms.HiddenInput(attrs={'id': 'lat'}),
                   'lon': forms.HiddenInput(attrs={'id': 'lon'}),
                   'start': SplitSelectDateTimeWidget(),
                   'end': SplitSelectDateTimeWidget()}
