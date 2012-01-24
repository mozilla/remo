import os
import tempfile

from django.conf import settings
from django.core import management, mail
from django.contrib.auth.models import User
from nose.tools import eq_
from test_utils import TestCase


class CreateUserTest(TestCase):
    """
    Create tests for create_user management command
    """

    def setUp(self):
        # check if actual email sending is enabled and if yes do not run
        if settings.EMAIL_BACKEND != 'django.core.mail.backends.locmem.EmailBackend':
            raise ValueError("Please change local.py to avoid "
                             "sending testing emails")

        # create a temporaty file with emails
        self.TEST_EMAILS = ["foo@example.com", "bar@example.com",
                            "bogusemail.com"]
        self.NO_VALID_EMAILS = 2
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)

        for email in self.TEST_EMAILS:
            self.temp_file.write(email)
            self.temp_file.write('\n')

        self.temp_file.close()

    def test_command_without_input_file(self):
        args = []
        opts = {}
        self.assertRaises(SystemExit, management.call_command,
                          'create_users', *args, **opts)


    def test_command_input_file_no_email(self):
        args = [self.temp_file.name]
        opts = {'email':False}
        management.call_command('create_users', *args, **opts)
        eq_(len(mail.outbox), 0)
        eq_(User.objects.count(), self.NO_VALID_EMAILS)


    def test_command_input_file_send_email(self):
        args = [self.temp_file.name]
        opts = {'email':True}
        management.call_command('create_users', *args, **opts)
        eq_(len(mail.outbox), self.NO_VALID_EMAILS)
        eq_(User.objects.count(), self.NO_VALID_EMAILS)


    def tearDown(self):
        os.unlink(self.temp_file.name)
