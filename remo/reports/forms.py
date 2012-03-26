from happyforms import forms

from models import Report, ReportComment, ReportEvent, ReportLink

ReportEventFormset = forms.models.inlineformset_factory(Report, ReportEvent,
                                                        extra=1)
ReportLinkFormset = forms.models.inlineformset_factory(Report, ReportLink,
                                                       extra=1)


class ReportForm(forms.ModelForm):
    """Form of a report."""
    delete_report = forms.BooleanField(required=False, initial=False)

    def clean(self):
        cleaned_data = super(ReportForm, self).clean()
        if (cleaned_data['future_items'] == '' and
            cleaned_data['past_items'] == ''):
            cleaned_data['empty'] = True
        else:
            cleaned_data['empty'] = False

        return cleaned_data

    class Meta:
        model = Report
        fields = ['empty', 'recruits_comments', 'past_items',
                  'future_items', 'flags', 'overdue']


class ReportCommentForm(forms.ModelForm):
    """Form of a report comment."""

    class Meta:
        model = ReportComment
        fields = ['comment']


class ReportEventForm(forms.ModelForm):
    """Form of report event."""

    class Meta:
        model = ReportEvent
        fields = ['name', 'description', 'link', 'participation_type']


class ReportLinkForm(forms.ModelForm):
    """Form of report link."""

    class Meta:
        model = ReportLink
        fields = ['description', 'link']
