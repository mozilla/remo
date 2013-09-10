from django.core.management.base import BaseCommand

from remo.reports.tasks import first_report_notification


class Command(BaseCommand):
    """Command to send reminder to all Reps to fill their reports."""
    help = 'Send email reminder to all Reps to fill their reports.'

    def handle(self, *args, **options):
        """Send first notifications to reps without a report,
        to submit the monthly report.

        """
        first_report_notification()
