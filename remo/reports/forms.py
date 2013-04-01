from happyforms import forms

from models import Report, ReportComment, ReportEvent, ReportLink

ReportEventFormset = forms.models.inlineformset_factory(Report, ReportEvent,
                                                        extra=1)
ReportLinkFormset = forms.models.inlineformset_factory(Report, ReportLink,
                                                       extra=1)


class ReportForm(forms.ModelForm):
    """Form of a report."""
    past_items = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'id': 'past_items',
                                     'class': 'flat',
                                     'placeholder': ('Summary or list of Rep '
                                                     'activities you were '
                                                     'involved in this past '
                                                     'month'),
                                     'cols': '',
                                     'rows': ''}))
    future_items = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'id': 'future_items',
                                     'class': 'flat',
                                     'placeholder': ('What Rep activity/ies '
                                                     'do you plan to be '
                                                     'involved in next '
                                                     'month?'),
                                     'cols': '',
                                     'rows': ''}))

    recruits_comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'id': 'recruits_comments',
                                     'class': 'flat',
                                     'placeholder': ('Were you successful '
                                                     'in recruiting new '
                                                     'Mozillians? If so, for '
                                                     'which project or '
                                                     'community?'),
                                     'cols': '',
                                     'rows': ''}))
    flags = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'id': 'flags',
                                     'class': 'flat',
                                     'placeholder': ('Notify your mentor '
                                                     'about any help you '
                                                     'might need or any '
                                                     'suggestions you might '
                                                     'have to improve the '
                                                     'program'),
                                     'cols': '',
                                     'rows': ''}))

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
