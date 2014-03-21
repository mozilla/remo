import datetime
import time

from django.contrib.auth.models import User
from django.utils.timezone import now

from cronjobs import register

from remo.reports.tasks import send_remo_mail
from remo.voting.models import Poll

# Intervals in seconds
NOTIFICATION_INTERVAL = 8 * 3600
EXTEND_VOTING_PERIOD = 24 * 3600


@register
def poll_vote_reminder():
    """Send an email reminder every 8 hours to
    remind valid users to cast their vote.

    """
    polls = Poll.objects.filter(start__lte=now(), end__gt=now())

    for poll in polls:
        last_notification = (poll.last_nofication if poll.last_notification
                             else poll.created_on)

        time_diff = (time.mktime(now().timetuple()) -
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
            Poll.objects.filter(pk=poll.pk).update(last_notification=now())


@register
def extend_voting_period():
    """Extend the voting period by 24hours if
    less than 50% of the Council members has voted
    and the poll ends in less than NOTIFICATION_INTERVAL.

    """
    polls = Poll.objects.filter(start__lte=now(), end__gt=now(),
                                automated_poll=True)

    for poll in polls:
        vote_count = poll.users_voted.all().count()
        missing_vote_count = (User.objects
                                  .filter(groups=poll.valid_groups)
                                  .exclude(pk__in=poll.users_voted.all())
                                  .count())
        half_voted = vote_count < missing_vote_count
        time_diff = (time.mktime(now().timetuple()) -
                     time.mktime(poll.end.timetuple()))
        if time_diff < NOTIFICATION_INTERVAL and half_voted:
            poll.end += datetime.timedelta(seconds=EXTEND_VOTING_PERIOD)
            poll.save()
