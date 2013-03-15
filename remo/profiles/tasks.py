from celery.task import task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


@task
def send_generic_mail(recipient_list, subject, email_template, data={}):
    """Send email to recipient_list rendered using email_template and populated
    with data.
    """
    data.update({'SITE_URL': settings.SITE_URL,
                 'FROM_EMAIL': settings.FROM_EMAIL})

    message = render_to_string(email_template, data)
    send_mail(subject, message, settings.FROM_EMAIL, recipient_list)
