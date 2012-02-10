import sys
import json
# alphabetiz imports

import requests

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.validators import email_re


class Command(BaseCommand):
    # Missing comment
    args = ''
    help = 'Fetch ReMo emails from wiki.mozilla.org'
    offset = 0
    URL = 'https://wiki.mozilla.org/api.php?action=ask&'\
          'q=[[Category:Remouser]]'\
          '&format=json&offset=%s&po=bugzillamail'


    def handle(self, *args, **options):
        # Missing comment
        while self.offset > -1:
            try:
                r = requests.get(self.URL % self.offset)

            except requests.ConnectionError:
                print "Connection Error"
                sys.exit(-1)

            if r.status_code != 200:
                print "Error fetching Wiki data"
                sys.exit(-1)

            try:
                data = json.loads(r.text)

            except ValueError, e:
                print r.text
                print "Error decoding Wiki data"
                sys.exit(-1)

            # convinience pointers
            results = data['ask']['results']
            query = data['ask']['query']

            # check offset
            if results.has_key('hasMore') and results['hasMore'] == 'true':
                self.offset += int(results['count']) + 1
            # remove this line break - keep conditions together.
            else:
                self.offset = -1

            for entry in results['items']:
                try:
                    email = entry['properties']['bugzillamail']

                except KeyError:
                    continue
                    # Do you want to output some message in the console
                    # when this exception occurs at least for debugging purposes?

                # sanitize input
                if not isinstance(email, basestring) or not email_re.match(email):
                    # ignoring invalid email
                    print "# Invalid email for %s" % entry['uri']
                    continue

                print email
