from calendar import monthrange
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now

import waffle
from celery.task import periodic_task, task

from remo.base.mozillians import is_vouched
from remo.base.tasks import send_remo_mail
from remo.base.utils import number2month
from remo.profiles.models import UserProfile


ROTM_REMINDER_DAY = 1


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
    place at the last day of each month.
    """

    now_date = now().date()
    days_of_month = monthrange(now_date.year, now_date.month)[1]
    if (now_date == date(now_date.year, now_date.month, days_of_month) or
            waffle.switch_is_active('enable_rotm_tasks')):
        nominees = UserProfile.objects.filter(is_rotm_nominee=True)
        for nominee in nominees:
            nominee.is_rotm_nominee = False
            nominee.save()


@task(run_every=timedelta(hours=24))
def send_rotm_nomination_reminder():
    """ Send an email reminder to all mentors.

    The first day of each month, the mentor group receives an email reminder
    in order to nominate Reps for the Rep of the month voting.
    """

    now_date = now().date()
    if now_date.day == ROTM_REMINDER_DAY:
        data = {'month': number2month(now_date.month)}
        subject = 'Nominate Rep of the month'
        template = 'emails/mentors_rotm_reminder.txt'
        send_remo_mail(subject=subject,
                       email_template=template,
                       recipients_list=[settings.REPS_MENTORS_LIST],
                       data=data)
