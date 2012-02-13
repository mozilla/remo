import json
import sys

from django.core.management.base import BaseCommand
from django.core.validators import email_re

import requests


class Command(BaseCommand):
    """ Command to fetch ReMo emails from wiki.mozilla.org using the API."""
    args = ''
    help = 'Fetch ReMo emails from wiki.mozilla.org'
    offset = 0
    URL = 'https://wiki.mozilla.org/api.php?action=ask&'\
          'q=[[Category:Remouser]]'\
          '&format=json&offset=%s&po=bugzillamail'

    def handle(self, *args, **options):
        """ Fetches users from wiki.mozilla.org.

        Prints the emails on stdout, one email per line
        """
        while self.offset > -1:
            try:
                r = requests.get(self.URL % self.offset)

            except requests.ConnectionError:
                self.stdout.write("Connection Error\n")
                sys.exit(-1)

            if r.status_code != 200:
                self.stdout.write("Error fetching Wiki data\n")
                sys.exit(-1)

            try:
                data = json.loads(r.text)

            except ValueError:
                self.stdout.write(r.text)
                self.stdout.write("Error decoding Wiki data\n")
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
                    self.stdout.write("# Error entry does not have"
                                      "bugzillamail: '%s'\n" %\
                                      json.dumps(entry))
                    continue

                # sanitize input
                if not isinstance(email, basestring) or\
                       not email_re.match(email):
                    # ignoring invalid email
                    self.stdout.write("# Invalid email for %s\n" %\
                                      entry['uri'])
                    continue

                self.stdout.write(email + '\n')
