from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.mail import send_mail
from django.template.loader import render_to_string

from celery.task import periodic_task, task
from celery.schedules import crontab

from remo.base.utils import go_back_n_months, number2month


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


@periodic_task(run_every=crontab())
def first_report_notification():
    """Notifies a group of users who have not submit
    their reports yet, to do so.

    """
    SUBJECT = '[Info] You can now file your Mozilla Reps monthly report for %s'
    EMAIL_TEMPLATE = 'emails/first_email_notification.txt'
    rep_group = Group.objects.get(name='Rep')
    reps = (rep_group.user_set
            .exclude(userprofile__registration_complete=False)
            .values_list('id', flat=True))
    date = go_back_n_months(datetime.today(), 1)
    month = number2month(date.month)
    subject = SUBJECT % month
    data = {'year': date.year, 'month': month}

    send_remo_mail(reps, subject, EMAIL_TEMPLATE, data)


@periodic_task(run_every=crontab())
def mentor_report_notification():
    """Notifies the mentors in case their mentees have not
    submitted their report for the previous month.

    """
    SUBJECT = '[Report] Your mentees with no reports for %s'
    EMAIL_TEMPLATE = 'emails/mentor_notification.txt'

    rep_group = Group.objects.get(name='Rep')
    reps = rep_group.user_set.exclude(
        userprofile__registration_complete=False)
    date = go_back_n_months(datetime.today(), 2)

    reps_without_report = reps.exclude(reports__month__year=date.year,
                                       reports__month__month=date.month)

    mentors = [rep.userprofile.mentor.id for rep in reps_without_report]

    month = number2month(date.month)
    subject = SUBJECT % month
    data = {'year': date.year, 'month': month,
            'reps_without_report': reps_without_report}

    send_remo_mail(mentors, subject, EMAIL_TEMPLATE, data)


@periodic_task(run_every=crontab())
def second_report_notification():
    """Send a second email notification to Reps who have not
    yet filled their reports.

    """

    SUBJECT = '[Reminder] Please file your Mozilla Reps monthly report for %s'
    EMAIL_TEMPLATE = 'emails/second_email_notification.txt'

    rep_group = Group.objects.get(name='Rep')
    reps = (rep_group.user_set
            .exclude(userprofile__registration_complete=False)
            .values_list('id', flat=True))
    date = go_back_n_months(datetime.today(), 1)
    reps_without_report = reps.exclude(reports__month__year=date.year,
                                       reports__month__month=date.month)

    month = number2month(date.month)
    subject = SUBJECT % month
    data = {'year': date.year, 'month': month}

    send_remo_mail(reps_without_report, subject, EMAIL_TEMPLATE, data)


@periodic_task(run_every=crontab())
def third_report_notification():
    """Send a third email notification to Reps who have not
    yet filled their reports."""
    SUBJECT = '[Reminder] Please file your Mozilla Reps monthly report for %s'
    EMAIL_TEMPLATE = 'emails/third_email_notification.txt'

    rep_group = Group.objects.get(name='Rep')
    reps = (rep_group.user_set
            .exclude(userprofile__registration_complete=False)
            .values_list('id', flat=True))
    date = go_back_n_months(datetime.today(), 2)

    reps_without_report = reps.exclude(reports__month__year=date.year,
                                       reports__month__month=date.month)

    month = number2month(date.month)
    subject = SUBJECT % month
    data = {'year': date.year, 'month': month}

    send_remo_mail(reps_without_report, subject, EMAIL_TEMPLATE, data)
