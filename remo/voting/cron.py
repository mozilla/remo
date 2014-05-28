import time
from datetime import timedelta

from django.contrib.auth.models import User
from django.utils.timezone import now

from cronjobs import register

from remo.base.tasks import send_remo_mail
from remo.base.utils import get_date
from remo.voting.models import Poll

NOTIFICATION_INTERVAL = 24 * 3600  # 24 hours
EXTEND_VOTING_PERIOD = 24 * 3600  # 24 hours


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
        if time_diff >= NOTIFICATION_INTERVAL:
            valid_users = User.objects.filter(groups=poll.valid_groups)
            recipients = (valid_users.exclude(pk__in=poll.users_voted.all())
                                     .values_list('id', flat=True))
            subject = ('[Reminder][Voting] Please cast your vote '
                       'for "%s" now!' % poll.name)
            template_reminder = 'emails/voting_vote_reminder.txt'
            ctx_data = {'poll': poll}
            send_remo_mail.delay(subject=subject, recipients_list=recipients,
                                 email_template=template_reminder,
                                 data=ctx_data)
            Poll.objects.filter(pk=poll.pk).update(last_notification=now())


@register
def extend_voting_period():
    """Extend voting period by EXTEND_VOTING_PERIOD if less than 50% of
    the Council has votes and the poll ends tomorrow.

    """
    tomorrow = get_date(days=1)
    polls = Poll.objects.filter(end__year=tomorrow.year,
                                end__month=tomorrow.month,
                                end__day=tomorrow.day,
                                automated_poll=True)

    for poll in polls:
        vote_count = poll.users_voted.all().count()
        missing_vote_count = (User.objects
                                  .filter(groups=poll.valid_groups)
                                  .exclude(pk__in=poll.users_voted.all())
                                  .count())
        half_voted = vote_count < missing_vote_count
        if half_voted:
            poll.end += timedelta(seconds=EXTEND_VOTING_PERIOD)
            poll.save()
