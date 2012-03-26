import json
import os
import StringIO
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core import management, mail
from nose.tools import eq_, raises
from test_utils import TestCase

import fudge
import requests

from remo.profiles.management.commands.fetch_emails_from_wiki import Command


class CreateUserTest(TestCase):
    """Tests for create_user management command."""
    fixtures = ['demo_users.json']

    def setUp(self):
        """Setup tests.

        Create an actual file in the filesystem with valid and
        invalid emails. Delete the file on exit.

        """
        # check if actual email sending is enabled and if yes do not run
        if (settings.EMAIL_BACKEND !=
            'django.core.mail.backends.locmem.EmailBackend'):
            raise ValueError('Please change local.py to avoid '
                             'sending testing emails')

        # create a temporaty file with emails
        self.TEST_EMAILS = ['foo@example.com', 'bar@example.com',
                            'bogusemail.com', 'foo@example.com']
        self.NUMBER_VALID_EMAILS = 2
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)

        self.number_of_users_in_db = User.objects.count()

        for email in self.TEST_EMAILS:
            self.temp_file.write(email)
            self.temp_file.write('\n')

        self.temp_file.close()

    def test_command_without_input_file(self):
        """Test that command exits with SystemExit exception when called
        without an input file.

        """
        args = []
        opts = {}
        self.assertRaises(SystemExit, management.call_command,
                          'create_users', *args, **opts)

    def test_command_input_file_no_email(self):
        """Test that users get successfully created and no email is sent."""
        args = [self.temp_file.name]
        opts = {'email': False}
        management.call_command('create_users', *args, **opts)
        eq_(len(mail.outbox), 0)
        eq_(User.objects.count(),
            self.NUMBER_VALID_EMAILS + self.number_of_users_in_db)

    def test_command_input_file_send_email(self):
        """Test that users get successfully created and emails are sent."""
        args = [self.temp_file.name]
        opts = {'email': True}
        management.call_command('create_users', *args, **opts)
        eq_(len(mail.outbox), self.NUMBER_VALID_EMAILS)
        eq_(User.objects.count(),
            self.NUMBER_VALID_EMAILS + self.number_of_users_in_db)

    def tearDown(self):
        """Cleanup Tests.

        Delete the temporary file with emails used during the tests.

        """
        os.unlink(self.temp_file.name)


class FetchEmailsFromWikiTest(TestCase):
    """Tests for fetch_emails_from_wiki management command."""

    @raises(SystemExit)
    @fudge.patch('requests.get')
    def test_command_with_connection_error(self, fake_requests_obj):
        """Test that command exits with SystemExit exception on connection
        error.

        """
        (fake_requests_obj.expects_call().raises(requests.ConnectionError))
        management.call_command('fetch_emails_from_wiki')

    @raises(SystemExit)
    @fudge.patch('requests.get')
    def test_command_with_invalid_code(self, fake_requests_obj):
        """Test that command exits with SystemExit exception on 404 error."""
        request = requests.Request()
        request.status_code = 404
        request.text = 'foo'
        (fake_requests_obj.expects_call().returns(request))
        management.call_command('fetch_emails_from_wiki')

    @raises(SystemExit)
    @fudge.patch('requests.get')
    def test_command_with_bogus_data(self, fake_requests_obj):
        """Test that command exits with SystemExit exception on json decode
        error.

        """
        request = requests.Request()
        request.status_code = 200
        request.text = 'foo'
        (fake_requests_obj.expects_call().returns(request))
        management.call_command('fetch_emails_from_wiki')

    @fudge.patch('requests.get')
    def test_command_with_valid_data(self, fake_requests_obj):
        """Test that command successfully fetches data and prints out
        emails.

        """
        request = requests.Request()
        request.status_code = 200
        request.text = json.dumps(
            {'ask':
             {'query': {},
              'results': {
                  'items':
                  [{'properties':{'bugzillamail':'foo@example.com'},
                     'uri': 'https:\/\/wiki.mozilla.org\/index.php?'
                            'title=User:fooexample'},
                   {'properties':{'bugzillamail':'test@example.com'},
                    'uri': 'https:\/\/wiki.mozilla.org\/index.php?'
                           'title=User:testexample'},
                   {'properties':{'bugzillamail':'testexample.com'},
                    'uri': 'https:\/\/wiki.mozilla.org\/index.php?'
                           'title=User:bogus'}]}}})

        (fake_requests_obj.expects_call().returns(request))

        output = StringIO.StringIO()
        cmd_obj = Command()
        cmd_obj.stdout = output
        cmd_obj.handle()

        # check each line of the output to ensure parsing
        lines = output.getvalue().split('\n')
        eq_(len(lines), 3)
        eq_(lines[0], 'foo@example.com')
        eq_(lines[1], 'test@example.com')
        eq_(lines[2], '')
