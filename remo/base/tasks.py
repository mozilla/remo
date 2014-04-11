from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.validators import email_re
from django.template.loader import render_to_string

from celery.task import task


@task
def send_remo_mail(subject, recipients_list, sender=None,
                   message=None, email_template=None, data=None,
                   headers=None):
    """Send email from /sender/ to /recipients_list/ with /subject/ and
    /message/ as body.

    """
    # Make sure that there is either a message or a template
    if not message and not email_template:
        return
    # Make sure that there is a recipient
    if not recipients_list:
        return
    if not headers:
        headers = {}
    if not sender:
        sender = settings.FROM_EMAIL
    if not data:
        data = {}
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
        elif email_re.match(recipient):
            to = recipient
        else:
            return

        if email_template:
            message = render_to_string(email_template, data)

        email = EmailMessage(subject=subject, body=message, from_email=sender,
                             to=[to], cc=[sender], headers=headers)
        email.send()
