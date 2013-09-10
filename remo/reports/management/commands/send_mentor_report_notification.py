from django.core.management.base import BaseCommand

from remo.reports.tasks import mentor_report_notification


class Command(BaseCommand):
    """Command to send email reminder to Mentors about Reps
    without reports.

    """
    help = 'Send email reminder to Mentors about Reps without reports.'

    def handle(self, *args, **options):
        """Send en email notification to mentors for mentees without
        a report for the previous month.

        """
        mentor_report_notification()
