import happyforms
from django import forms
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.timezone import make_naive, now
from product_details import product_details

from django_statsd.clients import statsd
from pytz import common_timezones, timezone

from remo.base.datetimewidgets import SplitSelectDateTimeWidget
from remo.base.templatetags.helpers import get_full_name
from remo.base.utils import get_date, get_object_or_none, validate_datetime
from remo.events.models import EventMetric
from remo.events.templatetags.helpers import get_event_link
from remo.profiles.models import FunctionalArea
from remo.reports import ACTIVITY_POST_EVENT_METRICS
from remo.reports.models import Activity, Campaign, NGReport
from remo.remozilla.models import Bug

from models import Event, EventComment, EventMetricOutcome


class MinBaseInlineFormSet(forms.models.BaseInlineFormSet):
    """Inline form-set support for minimum number of filled forms."""

    def __init__(self, *args, **kwargs):
        """Init formset with minimum number of 2 forms."""
        self.min_forms = kwargs.pop('min_forms', 2)
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
            raise ValidationError('You must fill at least %d forms' % self.min_forms)

        return super(MinBaseInlineFormSet, self).clean()


class BaseEventMetricsFormset(MinBaseInlineFormSet):
    """Inline form-set support for event metrics."""

    def __init__(self, *args, **kwargs):
        self.clone = kwargs.pop('clone', None)
        super(BaseEventMetricsFormset, self).__init__(*args, **kwargs)

    def clean(self):
        """Check for unique metrics inside formset."""
        super(BaseEventMetricsFormset, self).clean()

        if any(self.errors):
            # Do not check unless are fields are valid
            return

        # Disable adding new forms in post event form.
        if self.instance.is_past_event and self.instance.has_new_metrics and not self.clone:
            if self.extra_forms and len(self.extra_forms) > 2:
                error_msg = 'You cannot add new metrics in a past event.'
                raise ValidationError(error_msg)
            if [key for key in self.cleaned_data if key.get('DELETE')]:
                error_msg = 'You cannot delete metrics in a past event.'
                raise ValidationError(error_msg)

        metrics = []
        field_error_msg = 'This metric has already been selected.'
        for i, form in enumerate(self.forms):
            if 'metric' in form.cleaned_data:
                metric = form.cleaned_data['metric']
                if metric in metrics:
                    self.errors[i]['metric'] = field_error_msg
                metrics.append(metric)

    def save_existing(self, form, instance, commit=True):
        """Override save_existing on cloned event to save metrics"""
        if self.clone:
            form.instance.id = None
            return self.save_new(form)
        return super(BaseEventMetricsFormset, self).save_existing(form, instance, commit)

    def save(self, *args, **kwargs):
        """Override save on cloned events."""
        if self.clone:
            for form in self.initial_forms:
                form.changed_data.append('id')
        return super(BaseEventMetricsFormset, self).save()


class EventMetricsForm(happyforms.ModelForm):
    """EventMetrics form."""
    metric = forms.ModelChoiceField(queryset=EventMetric.active_objects.all(),
                                    empty_label='Please select an event metric.')
    expected_outcome = forms.IntegerField(error_messages={'invalid': 'Please enter a number.'})

    class Meta:
        model = EventMetricOutcome
        fields = ('metric', 'expected_outcome')

    def __init__(self, *args, **kwargs):
        """Dynamically initialize form."""
        self.clone = kwargs.pop('clone', None)
        super(EventMetricsForm, self).__init__(*args, **kwargs)

        if self.instance.id:
            # Dynamic queryset for active metrics in saved events
            current_metrics = self.instance.event.metrics.all()
            metrics_query = Q(active=True) | Q(pk__in=current_metrics)
            qs = EventMetric.objects.filter(metrics_query)
            self.fields['metric'].queryset = qs

    def save(self, *args, **kwargs):
        """Override save method to handle metrics cloning."""
        if self.clone:
            self.instance.pk = None
            self.instance.outcome = None
            self.instance.details = ''
        return super(EventMetricsForm, self).save(*args, **kwargs)


class PostEventMetricsForm(EventMetricsForm):
    """PostEventMetrics form."""
    outcome = forms.IntegerField(error_messages={'invalid': 'Please enter a number.'})

    class Meta(EventMetricsForm.Meta):
        fields = ('metric', 'expected_outcome', 'outcome', 'details')

    def __init__(self, *args, **kwargs):
        """Make expected outcome readonly."""
        super(PostEventMetricsForm, self).__init__(*args, **kwargs)
        if self.instance.expected_outcome:
            self.fields['expected_outcome'].widget.attrs['readonly'] = True


class EventForm(happyforms.ModelForm):
    """Form of an event."""
    categories = forms.ChoiceField(choices=[])
    country = forms.ChoiceField(
        choices=[],
        error_messages={'required': 'Please select one option from the list.'})
    swag_bug_form = forms.CharField(required=False)
    budget_bug_form = forms.CharField(required=False)
    estimated_attendance = forms.IntegerField(
        validators=[MinValueValidator(1)],
        error_messages={'invalid': 'Please enter a number.'})
    owner = forms.IntegerField(required=False)
    timezone = forms.ChoiceField(choices=zip(common_timezones, common_timezones))
    start = forms.DateTimeField(required=False)
    end = forms.DateTimeField(required=False)
    campaign = forms.ModelChoiceField(queryset=Campaign.active_objects.all())

    def __init__(self, *args, **kwargs):
        """Initialize form.

        Dynamically set choices for country field.
        """
        if 'editable_owner' in kwargs:
            self.editable_owner = kwargs['editable_owner']
            del(kwargs['editable_owner'])

        self.clone = kwargs.pop('clone', None)
        self.user = kwargs.pop('user', None)
        super(EventForm, self).__init__(*args, **kwargs)

        # Dynamic categories field.
        categories_query = FunctionalArea.objects.filter(Q(active=True))

        if self.instance.id and self.instance.categories.all():
            categories_query |= categories_query.filter(Q(id__in=self.instance.categories.all()))
            initial_category = self.instance.categories.all()[0]
            self.fields['categories'].initial = initial_category.id

        categories = ([('', 'Please select a functional area')] +
                      list(categories_query.values_list('id', 'name')))
        self.fields['categories'].choices = categories

        # Intiatives/Campaign field
        self.fields['campaign'].empty_label = 'Please select an initiative.'

        # Dynamic countries field.
        countries = product_details.get_regions('en').values()
        countries.sort()
        country_choices = ([('', 'Country')] +
                           [(country, country) for country in countries])
        self.fields['country'].choices = country_choices

        # Dynamic owner field.
        initial_user = self.instance.owner
        if self.clone:
            initial_user = self.user
        if self.editable_owner:
            self.fields['owner_form'] = forms.ModelChoiceField(
                queryset=User.objects.filter(userprofile__registration_complete=True,
                                             groups__name='Rep').order_by('first_name'),
                empty_label='Owner', initial=initial_user.id)
        else:
            self.fields['owner_form'] = forms.CharField(required=False,
                                                        initial=get_full_name(initial_user),
                                                        widget=forms.TextInput(
                                                            attrs={'readonly': 'readonly',
                                                                   'class': 'input-text big'}))

        instance = self.instance
        # Dynamically set the year portion of the datetime widget
        start_year = min(getattr(self.instance.start, 'year', now().year), now().year - 1)
        end_year = min(getattr(self.instance.end, 'year', now().year), now().year - 1)

        self.fields['start_form'] = forms.DateTimeField(widget=SplitSelectDateTimeWidget(
            years=range(start_year, start_year + 10), minute_step=5),
            validators=[validate_datetime])
        self.fields['end_form'] = forms.DateTimeField(widget=SplitSelectDateTimeWidget(
            years=range(end_year, end_year + 10), minute_step=5),
            validators=[validate_datetime])
        # Make times local to venue
        if self.instance.start:
            start = make_naive(instance.local_start, timezone(instance.timezone))
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
        if not all(k in cdata for k in ('start_form', 'end_form')):
            raise ValidationError('Please correct the form errors.')
        # Set timezone
        t = timezone(cdata['timezone'])
        start = make_naive(cdata['start_form'], timezone(settings.TIME_ZONE))
        cdata['start'] = t.localize(start)
        end = make_naive(cdata['end_form'], timezone(settings.TIME_ZONE))
        cdata['end'] = t.localize(end)

        # Do not allow cloning with a past date
        if cdata['start'] < now() and self.clone:
            msg = 'Start date in a cloned event cannot be in the past.'
            self._errors['start_form'] = self.error_class([msg])

        if cdata['start'] >= cdata['end']:
            msg = 'Start date should come before end date.'
            self._errors['start_form'] = self.error_class([msg])

        # Check that there is a cateogry selected
        if not cdata.get('categories'):
            msg = 'You need to select one functional area for this event.'
            self._errors['categories'] = self.error_class([msg])

        return cdata

    def _clean_bug(self, bug_id):
        """Get or create Bug with bug_id and component. """
        if bug_id == '':
            return None

        try:
            bug_id = int(bug_id)
        except ValueError:
            raise ValidationError('Please provide a number')

        bug, created = Bug.objects.get_or_create(bug_id=bug_id)
        return bug

    def clean_categories(self):
        category_id = self.cleaned_data['categories']
        return get_object_or_none(FunctionalArea, id=category_id)

    def clean_swag_bug_form(self):
        """Clean swag_bug_form field."""
        data = self.cleaned_data['swag_bug_form']
        return self._clean_bug(data)

    def clean_budget_bug_form(self):
        """Clean budget_bug_form field."""
        data = self.cleaned_data['budget_bug_form']
        return self._clean_bug(data)

    def save(self, commit=True):
        """Override save method for custom functionality."""
        event = super(EventForm, self).save(commit=False)
        if self.clone:
            event.pk = None
            event.has_new_metrics = True
            event.actual_attendance = None
            event.times_edited = 0
            event.owner = self.user
        elif self.instance.pk:
            # It's not either a clone event nor a new one,
            # please increment number of event edits
            event.times_edited += 1
        event.save()
        # Clear all relations in order to force only one field
        event.categories.clear()
        event.categories.add(self.cleaned_data['categories'])
        return event

    class Meta:
        model = Event
        fields = ['name', 'start', 'end', 'venue', 'region', 'owner',
                  'country', 'city', 'lat', 'lon', 'external_link',
                  'planning_pad_url', 'timezone', 'estimated_attendance',
                  'description', 'extra_content', 'hashtag', 'mozilla_event',
                  'swag_bug', 'budget_bug', 'campaign']
        widgets = {'lat': forms.HiddenInput(attrs={'id': 'lat'}),
                   'lon': forms.HiddenInput(attrs={'id': 'lon'}),
                   'start': SplitSelectDateTimeWidget(),
                   'end': SplitSelectDateTimeWidget()}


class PostEventForm(EventForm):
    """Post event form."""
    actual_attendance = forms.IntegerField(validators=[MinValueValidator(1)],
                                           error_messages={'invalid': 'Please enter a number.'})

    def save(self, *args, **kwargs):
        """Create post event data report."""
        event = super(PostEventForm, self).save()

        activity = Activity.objects.get(name=ACTIVITY_POST_EVENT_METRICS)
        reports = NGReport.objects.filter(event=event, activity=activity)

        if not reports:
            up = event.owner.userprofile
            attrs = {
                'activity': activity,
                'report_date': get_date(),
                'longitude': up.lon,
                'latitude': up.lat,
                'location': '%s, %s, %s' % (up.city, up.region, up.country),
                'link': get_event_link(event),
                'is_passive': True,
                'event': event,
                'user': event.owner
            }

            report = NGReport.objects.create(**attrs)
            report.functional_areas.add(*event.categories.all())
            statsd.incr('reports.create_passive_post_event_metrics')

        return event

    class Meta(EventForm.Meta):
        fields = EventForm.Meta.fields + ['actual_attendance']

    def __init__(self, *args, **kwargs):
        """Make estimated attendance readonly."""
        super(PostEventForm, self).__init__(*args, **kwargs)
        self.fields['estimated_attendance'].widget.attrs['readonly'] = True


class EventCommentForm(happyforms.ModelForm):
    """Form of an event comment."""

    class Meta:
        model = EventComment
        fields = ['comment']


class EventMetricForm(happyforms.ModelForm):
    """Form for EventMetric Model."""

    class Meta:
        model = EventMetric
        fields = ['name', 'active']
