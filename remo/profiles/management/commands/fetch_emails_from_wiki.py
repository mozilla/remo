import json
import logging
import sys

from django.core.management.base import BaseCommand
from django.core.validators import email_re

import requests

LOGGER = logging.getLogger("playdoh")


class Command(BaseCommand):
    """Command to fetch ReMo emails from wiki.mozilla.org using the API."""
    args = ''
    help = 'Fetch ReMo emails from wiki.mozilla.org'
    offset = 0
    URL = ('https://wiki.mozilla.org/api.php?action=ask&'
           'q=[[Category:Remouser]]'
           '&format=json&offset=%s&po=bugzillamail')

    def handle(self, *args, **options):
        """Fetches users from wiki.mozilla.org.

        Prints the emails on stdout, one email per line.

        """
        while self.offset > -1:
            try:
                r = requests.get(self.URL % self.offset)

            except requests.ConnectionError:
                LOGGER.error('Connection Error.')
                sys.exit(-1)

            if r.status_code != 200:
                LOGGER.error('Error fetching wiki data.')
                sys.exit(-1)

            try:
                data = json.loads(r.text)

            except ValueError:
                LOGGER.error('Error decoding wiki data.')
                sys.exit(-1)

            # convenience pointers
            results = data['ask']['results']

            # check offset
            if 'hasMore' in results and results['hasMore'] == 'true':
                self.offset += int(results['count']) + 1
            else:
                self.offset = -1

            for entry in results['items']:
                try:
                    email = entry['properties']['bugzillamail']
                except KeyError:
                    LOGGER.warning('# Error entry does not have '
                                   'bugzillamail: %s' % json.dumps(entry))
                    continue

                # sanitize input
                if (not isinstance(email, basestring) or
                    not email_re.match(email)):
                    # ignoring invalid email
                    LOGGER.warning('# Invalid email: %s' % entry['uri'])
                    continue

                self.stdout.write(email + '\n')
