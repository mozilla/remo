from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.validators import email_re
from django.template.loader import render_to_string

from celery.task import task


@task
def send_remo_mail(subject, recipients_list, sender=None,
                   message=None, email_template=None, data=None,
                   headers=None, bcc=False):
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
    if not data:
        data = {}
    data.update({'SITE_URL': settings.SITE_URL,
                 'FROM_EMAIL': settings.FROM_EMAIL})

    # Make sure subject is one line.
    subject = subject.replace('\n', ' ')

    # Prepare the list of recipients
    list_of_recipients = []
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
            continue
        list_of_recipients.append(to)

    if email_template:
        message = render_to_string(email_template, data)

    if not list_of_recipients:
        return

    kwargs = {'subject': subject,
              'body': message,
              'headers': headers,
              'from_email': settings.FROM_EMAIL,
              'to': list_of_recipients}

    if sender:
        kwargs['from_email'] = sender
        kwargs['cc'] = [sender]

    if bcc and (len(list_of_recipients) > 1):
        kwargs['to'] = [list_of_recipients.pop(0)]
        kwargs['bcc'] = list_of_recipients

    EmailMessage(**kwargs).send()
