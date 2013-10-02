from django.core.management.base import BaseCommand

from remo.reports.tasks import second_report_notification


class Command(BaseCommand):
    """Command to send second email reminder to Reps who haven't yet
    filled their reports.

    """
    help = 'Send email reminder to Reps who haven\'t yet filled their reports.'

    def handle(self, *args, **options):
        """Send the second notification to Reps to submit their reports."""
        second_report_notification()
