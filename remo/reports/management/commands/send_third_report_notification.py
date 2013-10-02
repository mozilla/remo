from django.core.management.base import BaseCommand

from remo.reports.tasks import third_report_notification


class Command(BaseCommand):
    """Command to send third email reminder to Reps who haven't yet
    filled their reports.

    """
    help = 'Send email reminder to Reps who haven\'t yet filled their reports.'

    def handle(self, *args, **options):
        """Sends the third notification to Reps to submit their reports."""
        third_report_notification()
