from happyforms import forms


class EmailMenteesForm(forms.Form):
    """Form to email mentees."""
    email_of_mentor = forms.CharField(
        required=False, label='',
        widget=forms.TextInput(attrs={'readonly': 'readonly',
                                      'class': 'input-text big'}))
    subject = forms.CharField(
        label='', widget=forms.TextInput(attrs={'placeholder': 'Subject',
                                                'required': 'required',
                                                'class': 'input-text big'}))
    body = forms.CharField(
        label='', widget=forms.Textarea(attrs={'placeholder': 'Body of email',
                                               'required': 'required',
                                               'class': 'flat long'}))
