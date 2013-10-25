import datetime

from django.core import management, mail
from nose.tools import eq_
from test_utils import TestCase

from mock import patch

from remo.reports.models import Report


class FirstNotificationTest(TestCase):
    """Test sending of first notification to Reps to fill reports."""
    fixtures = ['demo_users.json', 'demo_reports.json']

    def test_send_notification(self):
        """Test sending of first notification to Reps to fill reports."""
        management.call_command('send_first_report_notification', [], {})
        eq_(len(mail.outbox), 4)


class SecondNotificationTest(TestCase):
    """Test sending of second notification to Reps to fill reports."""
    fixtures = ['demo_users.json', 'demo_reports.json']

    @patch('remo.reports.management.commands'
           '.send_second_report_notification.datetime')
    def test_send_notification_with_reports_filled(self, fake_datetime):
        """Test sending of second notification, with reports filled."""
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        fake_datetime.today.return_value = fake_date

        management.call_command('send_second_report_notification', [], {})
        eq_(len(mail.outbox), 3)

    @patch('remo.reports.management.commands'
           '.send_second_report_notification.datetime')
    def test_send_notification_without_reports_filled(self, fake_datetime):
        """Test sending of second notification, with missing reports."""
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        fake_datetime.today.return_value = fake_date

        # delete existing reports
        Report.objects.all().delete()
        management.call_command('send_second_report_notification', [], {})
        eq_(len(mail.outbox), 4)


class ThirdNotificationTest(TestCase):
    """Test sending of third notification to Reps to fill reports."""
    fixtures = ['demo_users.json', 'demo_reports.json']

    @patch('remo.reports.management.commands'
           '.send_third_report_notification.datetime')
    def test_send_notification_with_reports_filled(self, fake_datetime):
        """Test sending of second notification, with reports filled."""
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        fake_datetime.today.return_value = fake_date

        management.call_command('send_third_report_notification', [], {})
        eq_(len(mail.outbox), 3)

    @patch('remo.reports.management.commands'
           '.send_third_report_notification.datetime')
    def test_send_notification_without_reports_filled(self, fake_datetime):
        """Test sending of second notification, with missing reports."""
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        fake_datetime.today.return_value = fake_date

        # delete existing reports
        Report.objects.all().delete()
        management.call_command('send_third_report_notification', [], {})
        eq_(len(mail.outbox), 4)


class MentorNotificationTest(TestCase):
    """Test sending reports to Mentors about unfilled reports."""
    fixtures = ['demo_users.json', 'demo_reports.json']

    @patch('remo.reports.management.commands'
           '.send_mentor_report_notification.datetime')
    def test_send_notification_with_reports_filled(self, fake_datetime):
        """Test sending of mentor notification, with reports filled."""
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        fake_datetime.today.return_value = fake_date

        management.call_command('send_mentor_report_notification', [], {})
        eq_(len(mail.outbox), 3)

    @patch('remo.reports.management.commands'
           '.send_mentor_report_notification.datetime')
    def test_send_notification_without_reports_filled(self, fake_datetime):
        """Test sending of second notification, with reports missing."""
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        fake_datetime.today.return_value = fake_date

        # delete existing reports
        Report.objects.all().delete()
        management.call_command('send_mentor_report_notification', [], {})
        eq_(len(mail.outbox), 4)
