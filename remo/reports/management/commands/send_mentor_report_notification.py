import datetime

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from remo.base.utils import number2month
from remo.reports.tasks import send_remo_mail
from remo.base.utils import go_back_n_months


class Command(BaseCommand):
    """Command to send email reminder to Mentors about Reps
    without reports.

    """
    help = 'Send email reminder to Mentors about Reps without reports.'
    SUBJECT = '[Report] Your mentees with no reports for %s'
    EMAIL_TEMPLATE = 'emails/mentor_notification.txt'

    def handle(self, *args, **options):
        """Prepares a list of reps to be notified and the required
        template variables.

        """
        rep_group = Group.objects.get(name='Rep')
        reps = rep_group.user_set.exclude(
            userprofile__registration_complete=False)
        date = go_back_n_months(datetime.datetime.today(), 2)

        reps_without_report = reps.exclude(reports__month__year=date.year,
                                           reports__month__month=date.month)

        mentors = [rep.userprofile.mentor for rep in reps_without_report]

        month = number2month(date.month)
        subject = self.SUBJECT % month
        data = {'year': date.year, 'month': month,
                'reps_without_report': reps_without_report}

        send_remo_mail(mentors, subject, self.EMAIL_TEMPLATE, data)
