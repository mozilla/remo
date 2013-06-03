from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string


@task()
def send_remo_mail(user_ids_list, subject, email_template, data=None):
    """Send to user_list emails based rendered using email_template
    and populated with data.

    """
    if not data:
        data = {}

    data.update({'SITE_URL': settings.SITE_URL,
                 'FROM_EMAIL': settings.FROM_EMAIL})

    for user_id in user_ids_list:
        if User.objects.filter(pk=user_id).exists():
            user = User.objects.get(pk=user_id)
            ctx_data = {'user': user,
                        'userprofile': user.userprofile}
            ctx_data.update(data)
            message = render_to_string(email_template, ctx_data)
            send_mail(subject, message, settings.FROM_EMAIL, [user.email])
