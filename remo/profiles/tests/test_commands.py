import os
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core import management, mail

from nose.tools import eq_

from remo.base.tests import RemoTestCase


class CreateUserTest(RemoTestCase):
    """Tests for create_user management command."""

    def setUp(self):
        """Setup tests.

        Create an actual file in the filesystem with valid and
        invalid emails. Delete the file on exit.

        """
        # check if actual email sending is enabled and if yes do not run
        if ((settings.EMAIL_BACKEND !=
             'django.core.mail.backends.locmem.EmailBackend')):
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


class CronjobsTest(RemoTestCase):
    """Tests for cronjobs management command."""

    def test_new_reps_reminder(self):
        """Test monthly email reminder for new reps."""

        args = ['new_reps_reminder']
        management.call_command('cron', *args)
        eq_(len(mail.outbox), 1)

        reminder = mail.outbox[0]
        eq_(reminder.from_email, settings.FROM_EMAIL)
        eq_(reminder.to, [settings.REPS_MENTORS_LIST])
