from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.template.loader import render_to_string

import requests

from remo.celery import app


@app.task
def send_remo_mail(subject, recipients_list, sender=None,
                   message=None, email_template=None, data=None,
                   headers=None):
    """Send email from /sender/ to /recipients_list/ with /subject/ and
    /message/ as body.

    """
    # Make sure that there is either a message or a template
    if not data:
        data = {}
    # If there is no body for the email and not a template
    # to render, then do nothing.
    if not message and not email_template:
        return
    # If there is both an email body, submitted by the user,
    # and a template to render as email body, then add
    # user's input to extra_content key
    elif message and email_template:
        data.update({'extra_content': message})
    # Make sure that there is a recipient
    if not recipients_list:
        return
    if not headers:
        headers = {}
    data.update({'SITE_URL': settings.SITE_URL,
                 'FROM_EMAIL': settings.FROM_EMAIL})

    # Make sure subject is one line.
    subject = subject.replace('\n', ' ')

    for recipient in recipients_list:
        to = ''
        if (isinstance(recipient, long) and
                User.objects.filter(pk=recipient).exists()):
            user = User.objects.get(pk=recipient)
            to = '%s <%s>' % (user.get_full_name(), user.email)
            ctx_data = {'user': user,
                        'userprofile': user.userprofile}
            data.update(ctx_data)
        else:
            try:
                validate_email(recipient)
                to = recipient
            except forms.ValidationError:
                return

        if email_template:
            message = render_to_string(email_template, data)

        email_data = {
            'subject': subject,
            'body': message,
            'from_email': settings.FROM_EMAIL,
            'to': [to],
        }

        if sender:
            # If there is a sender, add a Reply-To header and send a copy to the sender
            headers.update({'Reply-To': sender})
            email_data.update({'cc': [sender]})

        # Add the headers to the mail data
        email_data.update({'headers': headers})
        # Send the email
        EmailMessage(**email_data).send()


@app.task
def celery_healthcheck():
    """Ping healthchecks.io periodically to monitor celery/celerybeat health."""

    response = requests.get(settings.HEALTHCHECKS_IO_URL)
    return response.status_code == requests.codes.ok
