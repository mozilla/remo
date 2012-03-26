from celery.decorators import task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


@task()
def send_remo_mail(user_list, subject, email_template, data = {}):
    """Send to user_list emails based rendered using email_template
    and populated with data.

    """
    data.update({'SITE_URL': settings.SITE_URL,
                 'FROM_EMAIL': settings.FROM_EMAIL})

    for user in user_list:
        ctx_data = {'user': user,
                    'userprofile': user.userprofile}
        ctx_data.update(data)
        message = render_to_string(email_template, ctx_data)
        send_mail(subject, message, settings.FROM_EMAIL, [user.email])
