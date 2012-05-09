from celery.decorators import task
from django.core.mail import send_mail


@task()
def send_mail_task(sender, recipients, subject, message):
    """Send email from /sender/ to /recipients/ with /subject/ and
    /message/ as body.

    """

    # Make sure subject is one line.
    subject = subject.replace('\n', ' ')

    send_mail(subject, message, sender, recipients)
