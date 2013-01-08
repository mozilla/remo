from django.contrib import messages
from django.contrib.auth.models import User
from happyforms import forms

from remo.base.tasks import send_mail_task


class EmailMenteesForm(forms.Form):
    """Form to email mentees."""
    def __init__(self, user, *args, **kwargs):
        """Initialize form.

        Dynamically set fields for the recipients of the mail.
        """
        super(EmailMenteesForm, self).__init__(*args, **kwargs)
        mentees = (User.objects.filter(userprofile__mentor=user).
                   values_list('first_name', 'last_name', 'email'))
        for first_name, last_name, email in mentees:
            self.fields['%s %s <%s>' %
                        (first_name, last_name, email)] = forms.BooleanField(
                            initial=True, required=False,
                            widget=forms.CheckboxInput(
                                attrs={'class': 'input-text big'}))
        self.fields['subject'] = forms.CharField(label='',
            widget=forms.TextInput(attrs={'placeholder': 'Subject',
                                          'required': 'required',
                                          'class': 'input-text big'}))
        self.fields['body'] = forms.CharField(label='',
            widget=forms.Textarea(attrs={'placeholder': 'Body of email',
                                             'required': 'required',
                                             'class': 'flat long'}))

    def send_mail(self, request):
        """Send mail to mentees."""
        mentees = []
        for field in self.fields:
            if (isinstance(self.fields[field], forms.BooleanField) and
                self.cleaned_data[field]):
                mentees.append(field)
        if mentees:
            from_email = '%s <%s>' % (request.user.get_full_name(),
                                      request.user.email)
            send_mail_task.delay(sender=from_email,
                                 recipients=mentees,
                                 subject=self.cleaned_data['subject'],
                                 message=self.cleaned_data['body'])
            messages.success(request, 'Email sent successfully.')
        else:
            messages.error(request, ('Email not sent. Please select at '
                                     'least one recipient.'))
