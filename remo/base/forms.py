import happyforms

from django import forms
from django.contrib import messages

from remo.base.tasks import send_remo_mail
from remo.profiles.models import UserProfile


class BaseEmailUsersForm(happyforms.Form):
    """Base form to send email to multiple users."""
    subject = forms.CharField(label='', widget=(
        forms.TextInput(attrs={'placeholder': 'Subject',
                               'required': 'required',
                               'class': 'input-text big'})))
    body = forms.CharField(label='', widget=(
        forms.Textarea(attrs={'placeholder': 'Body of email',
                              'required': 'required',
                              'class': 'flat long'})))


class EmailUsersForm(BaseEmailUsersForm):
    """Generic form to send email to multiple users."""

    def __init__(self, users, *args, **kwargs):
        """Initialize form.

        Dynamically set fields for the recipients of the mail.
        """
        super(EmailUsersForm, self).__init__(*args, **kwargs)
        for user in users:
            # Insert method is used to override the order of form fields
            form_widget = forms.CheckboxInput(
                attrs={'class': 'input-text-big'})
            self.fields.insert(0, str(user.id),
                               forms.BooleanField(
                                   label=user,
                                   initial=False,
                                   required=False,
                                   widget=form_widget))

    def send_mail(self, request):
        """Send mail to recipients list."""
        recipients_list = []
        for field in self.fields:
            if (isinstance(self.fields[field], forms.BooleanField) and
                    self.cleaned_data[field]):
                recipients_list.append(long(field))

        if recipients_list:
            from_email = '%s <%s>' % (request.user.get_full_name(),
                                      request.user.email)
            send_remo_mail.delay(sender=from_email,
                                 recipients_list=recipients_list,
                                 subject=self.cleaned_data['subject'],
                                 message=self.cleaned_data['body'])
            messages.success(request, 'Email sent successfully.')
        else:
            messages.error(request, ('Email not sent. Please select at '
                                     'least one recipient.'))


class EmailMentorForm(BaseEmailUsersForm):
    """Generic form to send email to a user's mentor."""
    subject = forms.CharField(required=False)

    def send_email(self, request, subject='', message=None,
                   template=None, data=None):
        """Send an email to user's mentor"""
        mentor = request.user.userprofile.mentor
        from_email = '%s <%s>' % (request.user.get_full_name(),
                                  request.user.email)
        send_remo_mail.delay(sender=from_email,
                             recipients_list=[mentor.id],
                             subject=subject,
                             message=message,
                             email_template=template,
                             data=data)


class EditSettingsForm(happyforms.ModelForm):
    """Form to edit user settings regarding mail preferences."""
    receive_email_on_add_comment = forms.BooleanField(
        required=False, initial=True,
        label=('Receive email when a user comments on a report.'))
    receive_email_on_add_event_comment = forms.BooleanField(
        required=False, initial=True,
        label=('Receive email when a user comments on an event.'))
    receive_email_on_add_voting_comment = forms.BooleanField(
        required=False, initial=True,
        label=('Receive email when a user comments on an poll.'))

    class Meta:
        model = UserProfile
        fields = ['receive_email_on_add_comment',
                  'receive_email_on_add_event_comment',
                  'receive_email_on_add_voting_comment']
