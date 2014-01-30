from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now as now_utc

import happyforms

from remo.reports.models import (Activity, Campaign, NGReport, NGReportComment,
                                 Report, ReportComment, ReportEvent,
                                 ReportLink)


# Old reporting system
class ReportForm(happyforms.ModelForm):
    """Form of a report."""
    past_items = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={'id': 'past_items',
                   'class': 'flat',
                   'placeholder': ('Summary or list of Rep activities you '
                                   'were involved in this past month'),
                   'cols': '',
                   'rows': ''}))
    future_items = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={'id': 'future_items',
                   'class': 'flat',
                   'placeholder': ('What Rep activity/ies do you plan to be '
                                   'involved in next month?'),
                   'cols': '',
                   'rows': ''}))

    recruits_comments = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={'id': 'recruits_comments',
                   'class': 'flat',
                   'placeholder': ('Were you successful in recruiting new '
                                   'Mozillians? If so, for which project or '
                                   'community?'),
                   'cols': '',
                   'rows': ''}))
    flags = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={'id': 'flags',
                   'class': 'flat',
                   'placeholder': ('Notify your mentor about any help you '
                                   'might need or any suggestions you might '
                                   'have to improve the program'),
                   'cols': '',
                   'rows': ''}))

    def clean(self):
        cleaned_data = super(ReportForm, self).clean()
        if ((not cleaned_data['future_items'] and
             not cleaned_data['past_items'])):
            cleaned_data['empty'] = True
        else:
            cleaned_data['empty'] = False

        return cleaned_data

    class Meta:
        model = Report
        fields = ['empty', 'recruits_comments', 'past_items',
                  'future_items', 'flags', 'overdue']


class ReportCommentForm(happyforms.ModelForm):
    """Form of a report comment."""

    class Meta:
        model = ReportComment
        fields = ['comment']


class ReportEventForm(happyforms.ModelForm):
    """Form of report event."""

    class Meta:
        model = ReportEvent
        fields = ['name', 'description', 'link', 'participation_type']


class ReportLinkForm(happyforms.ModelForm):
    """Form of report link."""

    class Meta:
        model = ReportLink
        fields = ['description', 'link']


# New Generation reporting system
class NGReportForm(happyforms.ModelForm):
    report_date = forms.DateField(input_formats=['%d %B %Y'])

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
        if (activity and activity.name == 'Participated in a campaign'
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
