from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string


@task
def send_voting_mail(voting_id, subject, email_template):
    """Send to user_list emails based rendered using email_template
    and populated with data.

    """
    # avoid circular dependencies
    from remo.voting.models import Poll

    poll = Poll.objects.get(pk=voting_id)
    data = {'SITE_URL': settings.SITE_URL,
            'FROM_EMAIL': settings.FROM_EMAIL,
            'poll': poll}

    if poll.automated_poll:
        message = render_to_string(email_template, data)
        send_mail(subject, message, settings.FROM_EMAIL,
                  [settings.REPS_COUNCIL_LIST])
    else:
        user_list = User.objects.filter(groups=poll.valid_groups)

        for user in user_list:
            ctx_data = {'user': user,
                        'userprofile': user.userprofile}
            ctx_data.update(data)
            message = render_to_string(email_template, ctx_data)
            send_mail(subject, message, settings.FROM_EMAIL, [user.email])
