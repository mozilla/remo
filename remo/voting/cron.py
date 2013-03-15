import pytz
from datetime import datetime

from django.contrib.auth.models import User
from django.utils import timezone

from cronjobs import register

from remo.reports.tasks import send_remo_mail
from remo.voting.models import Poll


@register
def poll_vote_reminder():
    """Send an email reminder every 8 hours to
    remind valid users to cast their vote.
    """
    now = timezone.make_aware(datetime.now(), pytz.UTC)
    polls = Poll.objects.filter(start__lt=now, end__gt=now)

    for poll in polls:
        last_notification = (poll.last_nofication if poll.last_notification
                             else poll.created_on)
        if abs(now.hour - last_notification.hour) > 8:
            valid_users = User.objects.filter(groups__name=poll.valid_groups)
            recipients = list(set(valid_users) ^ set(poll.users_voted.all()))
            subject = ('[Reminder][Voting] Please cast your vote '
                       'for "%s" now!' % poll.name)
            template_reminder = 'emails/voting_vote_reminder.txt'
            ctx_data = {'poll': poll}
            send_remo_mail.delay(recipients, subject,
                                 template_reminder, ctx_data)
            poll.last_notification = now
            poll.save()
