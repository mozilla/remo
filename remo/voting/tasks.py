import time
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string

from celery.task import periodic_task, task

from remo.base.utils import datetime2pdt
from remo.reports.tasks import send_remo_mail

# Intervals in seconds
NOTIFICATION_INTERVAL = 8 * 3600
EXTEND_VOTING_PERIOD = 24 * 3600
INTERVAL = 15 * 60


@task
def send_voting_mail(voting_id, subject, email_template):
    """Send emails to the valid users of a poll with information
    about the start and end period of this poll.

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
                  [settings.REPS_COUNCIL_ALIAS])
    else:
        user_list = User.objects.filter(groups=poll.valid_groups)

        for user in user_list:
            ctx_data = {'user': user,
                        'userprofile': user.userprofile}
            ctx_data.update(data)
            message = render_to_string(email_template, ctx_data)
            send_mail(subject, message, settings.FROM_EMAIL, [user.email])


@periodic_task(run_every=timedelta(seconds=INTERVAL))
def poll_vote_reminder():
    """Send an email reminder every 8 hours to
    remind valid users to cast their vote.

    """
    # avoid circular dependencies
    from remo.voting.models import Poll

    now = datetime2pdt()
    polls = Poll.objects.filter(start__lte=now, end__gt=now)

    for poll in polls:
        last_notification = (poll.last_notification if poll.last_notification
                             else poll.created_on)

        time_diff = (time.mktime(now.timetuple()) -
                     time.mktime(last_notification.timetuple()))
        if time_diff > NOTIFICATION_INTERVAL:
            valid_users = User.objects.filter(groups=poll.valid_groups)
            recipients = (valid_users.exclude(pk__in=poll.users_voted.all())
                                     .values_list('id', flat=True))
            subject = ('[Reminder][Voting] Please cast your vote '
                       'for "%s" now!' % poll.name)
            template_reminder = 'emails/voting_vote_reminder.txt'
            ctx_data = {'poll': poll}
            send_remo_mail.delay(recipients, subject,
                                 template_reminder, ctx_data)
            Poll.objects.filter(pk=poll.pk).update(last_notification=now)


@periodic_task(run_every=timedelta(seconds=INTERVAL))
def extend_voting_period():
    """Extend the voting period by 24hours if
    less than 50% of the Council members has voted
    and the poll ends in less than NOTIFICATION_INTERVAL.

    """
    # avoid circular dependencies
    from remo.voting.models import Poll

    now = datetime2pdt()
    polls = Poll.objects.filter(start__lte=now, end__gt=now,
                                automated_poll=True)

    for poll in polls:
        vote_count = poll.users_voted.all().count()
        missing_vote_count = (User.objects
                                  .filter(groups=poll.valid_groups)
                                  .exclude(pk__in=poll.users_voted.all())
                                  .count())
        half_voted = vote_count < missing_vote_count
        time_diff = (time.mktime(now.timetuple()) -
                     time.mktime(poll.end.timetuple()))
        if time_diff < NOTIFICATION_INTERVAL and half_voted:
            poll.end += timedelta(seconds=EXTEND_VOTING_PERIOD)
            poll.save()
