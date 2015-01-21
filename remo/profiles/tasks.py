from calendar import monthrange
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now

from celery.task import periodic_task, task

from remo.base.mozillians import is_vouched
from remo.profiles.models import UserProfile


DAYS_OFFSET = 4


@task
def send_generic_mail(recipient_list, subject, email_template, data={}):
    """Send email to recipient_list rendered using email_template and populated
    with data.
    """
    data.update({'SITE_URL': settings.SITE_URL,
                 'FROM_EMAIL': settings.FROM_EMAIL})

    message = render_to_string(email_template, data)
    send_mail(subject, message, settings.FROM_EMAIL, recipient_list)


@periodic_task(run_every=timedelta(hours=24), soft_time_limit=300)
def check_mozillian_username():
    mozillians = User.objects.filter(groups__name='Mozillians')

    for user in mozillians:
        data = is_vouched(user.email)
        if data and data['is_vouched'] and 'full_name' in data:
            first_name, last_name = (
                data['full_name'].split(' ', 1)
                if ' ' in data['full_name']
                else ('', data['full_name']))
            user.first_name = first_name
            user.last_name = last_name
            user.userprofile.mozillian_username = data['username']
        else:
            user.first_name = 'Anonymous'
            user.last_name = 'Mozillian'
            user.userprofile.mozillian_username = ''
        user.save()
        user.userprofile.save()


@task(ignore_result=False)
def check_celery():
    """Dummy celery task to check that everything runs smoothly."""
    pass


@task(run_every=timedelta(hours=24))
def reset_rotm_nominees():
    """Reset the Rep of the month nomination in user profiles.

    This task will reset the nomination bit for the Rep of the month in the
    user profiles, for all the users nominated in each month. This will take
    place 4 days before the end of each month.
    """

    now_date = now().date()
    days_of_month = monthrange(now_date.year, now_date.month)[1]
    reset_poll_day = days_of_month - DAYS_OFFSET
    if now_date == date(now_date.year, now_date.month, reset_poll_day):
        nominees = UserProfile.objects.filter(is_rotm_nominee=True)
        for nominee in nominees:
            nominee.is_rotm_nominee = False
            nominee.save()
