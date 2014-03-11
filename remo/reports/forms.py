from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now as now_utc

import happyforms

from remo.reports import ACTIVITY_CAMPAIGN, UNLISTED_ACTIVITIES
from remo.reports.models import Activity, Campaign, NGReport, NGReportComment


# New Generation reporting system
class NGReportForm(happyforms.ModelForm):
    report_date = forms.DateField(input_formats=['%d %B %Y'])
    activity = forms.ModelChoiceField(
        queryset=Activity.active_objects.exclude(name__in=UNLISTED_ACTIVITIES))
    campaign = forms.ModelChoiceField(queryset=Campaign.active_objects.all(),
                                      required=False)

    def __init__(self, *args, **kwargs):
        """ Initialize form.

        Dynamically set the report date.
        """
        super(NGReportForm, self).__init__(*args, **kwargs)
        self.fields['activity'].empty_label = 'Please select an activity.'
        self.fields['activity'].error_messages['required'] = (
            'Please select an option from the list.')
        self.fields['campaign'].empty_label = 'Please select a campaign.'

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
        if self.cleaned_data['report_date'] > now_utc().date():
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
