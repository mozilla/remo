from celery.decorators import task
from django.core.mail import EmailMessage


@task()
def send_mail_task(sender, recipients, subject, message):
    """Send email from /sender/ to /recipients/ with /subject/ and
    /message/ as body.

    """

    # Make sure subject is one line.
    subject = subject.replace('\n', ' ')

    email = EmailMessage(subject=subject, body=message, from_email=sender,
                         to=recipients, cc=[sender])
    email.send()
