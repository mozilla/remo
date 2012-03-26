import datetime

from django.core import management, mail
from nose.tools import eq_
from test_utils import TestCase

import fudge

from remo.reports.models import Report


class FirstNotificationTest(TestCase):
    """Test sending of first notification to Reps to fill reports."""
    fixtures = ['demo_users.json', 'demo_reports.json']

    def test_send_notification(self):
        management.call_command('send_first_report_notification', [], {})
        eq_(len(mail.outbox), 1)


class SecondNotificationTest(TestCase):
    """Test sending of second notification to Reps to fill reports."""
    fixtures = ['demo_users.json', 'demo_reports.json']

    @fudge.patch('datetime.datetime.today')
    def test_send_notification_with_reports_filled(self, fake_requests_obj):
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        (fake_requests_obj.expects_call().returns(fake_date))

        management.call_command('send_second_report_notification', [], {})
        eq_(len(mail.outbox), 0)

    @fudge.patch('datetime.datetime.today')
    def test_send_notification_without_reports_filled(self, fake_requests_obj):
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        (fake_requests_obj.expects_call().returns(fake_date))

        # delete existing reports
        Report.objects.all().delete()
        management.call_command('send_second_report_notification', [], {})
        eq_(len(mail.outbox), 1)


class ThirdNotificationTest(TestCase):
    """Test sending of third notification to Reps to fill reports."""
    fixtures = ['demo_users.json', 'demo_reports.json']

    @fudge.patch('datetime.datetime.today')
    def test_send_notification_with_reports_filled(self, fake_requests_obj):
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        (fake_requests_obj.expects_call().returns(fake_date))

        management.call_command('send_third_report_notification', [], {})
        eq_(len(mail.outbox), 0)

    @fudge.patch('datetime.datetime.today')
    def test_send_notification_without_reports_filled(self, fake_requests_obj):
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        (fake_requests_obj.expects_call().returns(fake_date))

        # delete existing reports
        Report.objects.all().delete()
        management.call_command('send_third_report_notification', [], {})
        eq_(len(mail.outbox), 1)


class MentorNotificationTest(TestCase):
    """Test sending reports to Mentors about unfilled reports."""
    fixtures = ['demo_users.json', 'demo_reports.json']

    @fudge.patch('datetime.datetime.today')
    def test_send_notification_with_reports_filled(self, fake_requests_obj):
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        (fake_requests_obj.expects_call().returns(fake_date))

        management.call_command('send_mentor_report_notification', [], {})
        eq_(len(mail.outbox), 0)

    @fudge.patch('datetime.datetime.today')
    def test_send_notification_without_reports_filled(self, fake_requests_obj):
        # act like it's March 2012
        fake_date = datetime.datetime(year=2012, month=3, day=1)
        (fake_requests_obj.expects_call().returns(fake_date))

        # delete existing reports
        Report.objects.all().delete()
        management.call_command('send_mentor_report_notification', [], {})
        eq_(len(mail.outbox), 1)
