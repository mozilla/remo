from optparse import make_option

from django.core.management.base import BaseCommand

from remo.remozilla.tasks import fetch_bugs


class Command(BaseCommand):
    """Management command interface to fetch_bugs()."""
    args = None
    help = 'Fetch bugs from Bugzilla'
    option_list = list(BaseCommand.option_list) + [
        make_option('--days-back',
                    dest='days',
                    default=None,
                    help='Fetch bugs updated during the last number of days.')]

    def handle(self, *args, **options):
        """Command handler."""
        fetch_bugs(days=options['days'])
