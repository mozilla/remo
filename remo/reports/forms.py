from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.timezone import now

import happyforms

from remo.profiles.models import FunctionalArea
from remo.reports import ACTIVITY_CAMPAIGN, UNLISTED_ACTIVITIES
from remo.reports.models import Activity, Campaign, NGReport, NGReportComment


# New Generation reporting system
class NGReportForm(happyforms.ModelForm):
    report_date = forms.DateField(input_formats=['%d %B %Y'])
    activity = forms.ModelChoiceField(
        queryset=Activity.active_objects.exclude(name__in=UNLISTED_ACTIVITIES))
    campaign = forms.ModelChoiceField(queryset=Campaign.active_objects.all(),
                                      required=False)
    functional_areas = forms.ModelMultipleChoiceField(
        queryset=FunctionalArea.active_objects.all())

    def __init__(self, *args, **kwargs):
        """ Initialize form.

        Dynamically set the report date.
        """
        super(NGReportForm, self).__init__(*args, **kwargs)
        self.fields['activity'].empty_label = 'Please select an activity.'
        self.fields['activity'].error_messages['required'] = (
            'Please select an option from the list.')
        self.fields['campaign'].empty_label = 'Please select a campaign.'

        # Dynamic functional_areas field
        if self.instance.id:
            current_areas = self.instance.functional_areas.all()
            query = Q(active=True) | Q(id__in=current_areas)
            areas = FunctionalArea.objects.filter(query)
            self.fields['functional_areas'].queryset = areas

    def clean(self):
        """Clean Form."""
        super(NGReportForm, self).clean()
        cdata = self.cleaned_data

        activity = cdata.get('activity')
        if (activity and activity.name == ACTIVITY_CAMPAIGN
                and not cdata.get('campaign')):
            msg = 'Please select an option from the list.'
            self._errors['campaign'] = self.error_class([msg])

        return cdata

    def clean_report_date(self):
        """Clean report_date field."""
        if self.cleaned_data['report_date'] > now().date():
            raise ValidationError('Report date cannot be in the future.')
        return self.cleaned_data['report_date']

    class Meta:
        model = NGReport
        fields = ['report_date', 'activity', 'campaign',
                  'functional_areas', 'longitude', 'latitude', 'location',
                  'link', 'link_description', 'activity_description']
        widgets = {'longitude': forms.HiddenInput(),
                   'latitude': forms.HiddenInput(),
                   'functional_areas': forms.SelectMultiple()}


class NGVerifyReportForm(happyforms.ModelForm):
    """Form to verify a recruitment."""
    verified_recruitment = forms.BooleanField(
        required=False, initial=False,
        label=('I have verified this activity'))

    class Meta:
        model = NGReport
        fields = ['verified_recruitment']


class NGReportCommentForm(happyforms.ModelForm):
    """Model Form for new generation commenting system."""

    class Meta:
        model = NGReportComment
        fields = ['comment']
        widgets = {'comment': forms.TextInput()}


class ActivityForm(happyforms.ModelForm):
    """Form of activity type."""

    class Meta:
        model = Activity


class CampaignForm(happyforms.ModelForm):
    """Form of campaign type."""

    class Meta:
        model = Campaign
