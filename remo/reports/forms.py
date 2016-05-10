from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.timezone import now

import happyforms

from remo.profiles.models import FunctionalArea
from remo.reports import UNLISTED_ACTIVITIES
from remo.reports.models import Activity, Campaign, NGReport, NGReportComment


# New Generation reporting system
class NGReportForm(happyforms.ModelForm):
    report_date = forms.DateField(input_formats=['%d %B %Y'])
    activity = forms.ModelChoiceField(
        queryset=Activity.active_objects.exclude(name__in=UNLISTED_ACTIVITIES))
    campaign = forms.ModelChoiceField(queryset=Campaign.active_objects.all())
    functional_areas = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        """ Initialize form.

        Dynamically set the report date.
        """

        super(NGReportForm, self).__init__(*args, **kwargs)
        self.fields['activity'].empty_label = 'Please select an activity.'
        self.fields['activity'].error_messages['required'] = (
            'Please select an option from the list.')
        self.fields['campaign'].empty_label = 'Please select an initiative.'
        area_choices = FunctionalArea.active_objects.values_list('id', 'name')
        self.fields['functional_areas'].choices = area_choices

        # Dynamic functional_areas field
        if self.instance.id:
            current_areas = self.instance.functional_areas.all()
            query = Q(active=True) | Q(id__in=current_areas)
            areas = FunctionalArea.objects.filter(query)
            choices = areas.values_list('id', 'name')
            if self.instance.functional_areas.exists():
                initial_category = self.instance.functional_areas.all()[0]
            self.fields['functional_areas'].choices = choices
            self.fields['functional_areas'].initial = initial_category.id

    def clean_report_date(self):
        """Clean report_date field."""
        if self.cleaned_data['report_date'] > now().date():
            raise ValidationError('Report date cannot be in the future.')
        return self.cleaned_data['report_date']

    def save(self, *args, **kwargs):
        instance = super(NGReportForm, self).save(*args, **kwargs)

        # Manually save functional areas.
        # For compatibility reasons we are keeping functional areas
        # as m2m in the models but we are forcing through this form a
        # single entry in the m2m relation.
        area_pk = self.cleaned_data['functional_areas']
        area = FunctionalArea.objects.get(id=area_pk)
        instance.functional_areas.clear()
        instance.functional_areas.add(area)

        return instance

    class Meta:
        model = NGReport
        fields = ['report_date', 'activity', 'campaign',
                  'longitude', 'latitude', 'location',
                  'link', 'link_description', 'activity_description']
        widgets = {'longitude': forms.HiddenInput(),
                   'latitude': forms.HiddenInput()}


class NGVerifyReportForm(happyforms.ModelForm):
    """Form to verify a recruitment."""

    class Meta:
        model = NGReport
        fields = ['verified_activity']


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
        fields = ['name']


class CampaignForm(happyforms.ModelForm):
    """Form of campaign type."""

    class Meta:
        model = Campaign
        fields = ['name']
