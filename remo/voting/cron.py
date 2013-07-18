import datetime
import pytz

from django.contrib.auth.models import User
from django.utils import timezone

from cronjobs import register

from remo.reports.tasks import send_remo_mail
from remo.voting.models import Poll

NOTIFICATION_INTERVAL = 8 * 3600


@register
def poll_vote_reminder():
    """Send an email reminder every 8 hours to
    remind valid users to cast their vote.

    """
    now = timezone.make_aware(datetime.datetime.utcnow(), pytz.UTC)
    polls = Poll.objects.filter(start__lte=now, end__gt=now)

    for poll in polls:
        last_notification = (poll.last_nofication if poll.last_notification
                             else poll.created_on)

        if (now - last_notification).seconds > NOTIFICATION_INTERVAL:
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
