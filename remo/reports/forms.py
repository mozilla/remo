from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now as now_utc

import happyforms
import pytz
from remo.reports.models import (Activity, Campaign, NGReport, Report,
                                 ReportComment, ReportEvent, ReportLink)


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
    activity = forms.ModelChoiceField(
        queryset=Activity.objects.all(),
        empty_label='Please select an activity',
        error_messages={'required': 'Please select an option from the list.'})
    campaign = forms.ModelChoiceField(
        queryset=Campaign.objects.all(),
        empty_label='Please select a campaign',
        required=False)
    created_on = forms.DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        """ Initialize form.

        Dynamically set the report date.
        """
        super(NGReportForm, self).__init__(*args, **kwargs)
        self.fields['report_date'] = forms.DateField(
            input_formats=['%d %b %Y'],
            widget=forms.DateInput(attrs={'class': 'datepicker',
                                          'readonly': 'true'}))

        if self.instance.created_on:
            self.fields['report_date'].initial = self.instance.creation_date

    def clean(self):
        """Clean Form."""
        super(NGReportForm, self).clean()
        cdata = self.cleaned_data

        if 'report_date' not in cdata:
            raise ValidationError('Please correct the form errors.')

        creation_date = self.cleaned_data['report_date']
        creation_datetime = (datetime.combine(creation_date, now_utc().time())
                             .replace(tzinfo=pytz.UTC))
        cdata['created_on'] = creation_datetime
        if cdata['created_on'] > now_utc():
            msg = 'Report date cannot be in the future.'
            self._errors['report_date'] = self.error_class([msg])

        if ('activity' in cdata and
            cdata['activity'].name == 'Participated in a campaign'
                and not cdata['campaign']):
            msg = 'Please select an option from the list'
            self._errors['campaign'] = self.error_class([msg])

        return cdata

    class Meta:
        model = NGReport
        fields = ['created_on', 'activity', 'campaign', 'functional_areas',
                  'longitude', 'latitude', 'location', 'link',
                  'link_description', 'activity_description']
        widgets = {'longitude': forms.HiddenInput(attrs={'id': 'lon'}),
                   'latitude': forms.HiddenInput(attrs={'id': 'lat'}),
                   'functional_areas': forms.SelectMultiple(
                       attrs={'class': 'contribution-area'})}
