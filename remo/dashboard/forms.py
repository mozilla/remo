import happyforms

from django import forms
from django.contrib import messages

from remo.base.forms import BaseEmailUsersForm
from remo.base.tasks import send_remo_mail
from remo.profiles.models import FunctionalArea, UserProfile


class EmailRepsForm(BaseEmailUsersForm):
    """Generic form to send email to multiple users."""

    functional_area = forms.ModelChoiceField(
        queryset=FunctionalArea.active_objects.all(), empty_label=None,
        widget=forms.HiddenInput())

    def send_email(self, request, users):
        """Send mail to recipients list."""
        recipients = users.values_list('id', flat=True)

        if recipients:
            from_email = '%s <%s>' % (request.user.get_full_name(),
                                      request.user.email)
            send_remo_mail.delay(sender=from_email,
                                 recipients_list=recipients,
                                 subject=self.cleaned_data['subject'],
                                 message=self.cleaned_data['body'])
            messages.success(request, 'Email sent successfully.')
        else:
            messages.error(request, 'Email not sent. An error occured.')


class TrackFunctionalAreasForm(happyforms.ModelForm):
    """Form for tracking interests in functional areas for Mozillians."""

    class Meta:
        model = UserProfile
        fields = ['tracked_functional_areas']
