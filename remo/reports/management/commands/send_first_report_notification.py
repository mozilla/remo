import datetime

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from remo.base.utils import number2month
from remo.reports.tasks import send_remo_mail
from remo.base.utils import go_back_n_months

from optparse import make_option


class Command(BaseCommand):
    """Command to send reminder to all Reps to fill their reports."""
    help = 'Send email reminder to all Reps to fill their reports.'
    option_list = list(BaseCommand.option_list) + [
        make_option('--dry-run',
                    default=False,
                    action='store_true',
                    dest='dry_run',
                    help='Run the command without sending emails')]
    SUBJECT = '[Info] You can now file your Mozilla Reps monthly report for %s'
    EMAIL_TEMPLATE = 'emails/first_email_notification.txt'

    def handle(self, *args, **options):
        """Prepares a list of reps to be notified and the required
        template variables.

        """
        rep_group = Group.objects.get(name='Rep')
        reps = (rep_group.user_set
                .exclude(userprofile__registration_complete=False))
        id_reps = reps.values_list('id', flat=True)

        date = go_back_n_months(datetime.datetime.today(), 1)
        month = number2month(date.month)

        subject = self.SUBJECT % month
        data = {'year': date.year, 'month': month}

        if options['dry_run']:
            email_reps = reps.values_list('email', flat=True)
            for recipient in email_reps:
                msg = 'First notification sent to %s' % recipient
                print(msg)
        else:
            send_remo_mail(id_reps, subject, self.EMAIL_TEMPLATE, data)
