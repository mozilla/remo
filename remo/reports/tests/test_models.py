import datetime

from django.contrib.auth.models import User
from django.core import mail
from nose.tools import eq_
from test_utils import TestCase

import fudge

from remo.base.utils import go_back_n_months
from remo.profiles.models import UserProfile
from remo.reports.models import OVERDUE_DAY, Report, ReportComment


class ModelTest(TestCase):
    """Tests related to Reports Models."""
    fixtures = ['demo_users.json']

    def setUp(self):
        """Setup tests."""
        self.user = User.objects.get(username="rep")
        self.month_year = datetime.date(year=2012, month=1, day=10)
        self.report = Report(user=self.user, month=self.month_year)
        self.report.save()

    def test_mentor_set_for_new_report(self):
        """Test that report mentor field stays the same when user
        changes mentor.

        """
        eq_(self.report.mentor, self.user.userprofile.mentor)

        # Change user mentor and re-save the report. Report should
        # point to the first mentor.
        old_mentor = self.user.userprofile.mentor
        self.user.userprofile.mentor = User.objects.get(username="counselor")
        self.user.save()

        self.report.save()
        eq_(self.report.mentor, old_mentor)

    def test_overdue_true(self):
        """Test overdue report (first test)."""
        eq_(self.report.overdue, True)

    @fudge.patch('datetime.date.today')
    def test_overdue_true_2(self, fake_requests_obj):
        """Test overdue report (second test)."""
        today = datetime.datetime.today()

        # act like it's OVERDUE_DAY + 1
        fake_date = datetime.datetime(year=today.year, month=today.month,
                                      day=OVERDUE_DAY + 1)
        (fake_requests_obj.expects_call().returns(fake_date))

        month_year = go_back_n_months(today)
        report = Report.objects.create(user=self.user, month=month_year)
        eq_(report.overdue, True)

    def test_overdue_false(self):
        """Test not overdue report (first test)."""
        # Change report created_on, so report is not overdue
        month_year = datetime.date(year=2020, month=1, day=10)
        report = Report.objects.create(user=self.user, month=month_year)
        eq_(report.overdue, False)

    @fudge.patch('datetime.date.today')
    def test_overdue_false_2(self, fake_requests_obj):
        """Test not overdue report (first test)."""
        # marginal case
        today = datetime.datetime.today()

        # act like it's OVERDUE_DAY
        fake_date = datetime.datetime(year=today.year, month=today.month,
                                      day=OVERDUE_DAY)
        (fake_requests_obj.expects_call().returns(fake_date))

        month_year = go_back_n_months(today)
        report = Report.objects.create(user=self.user, month=month_year)
        eq_(report.overdue, False)

    def test_set_month_day(self):
        """Test that reports month always points to first day of the month."""
        eq_(self.report.month.day, 1)


class MentorNotificationOnAddEditReport(TestCase):
    """Test that a Mentor receives an email when a Mentee
    adds/edits a report.
    """
    fixtures = ['demo_users.json', 'demo_reports.json']

    def setUp(self):
        self.date = datetime.datetime.now()
        self.user = User.objects.get(username='rep')
        self.new_report = Report(user=self.user, month=self.date)
        self.edit_report = self.user.reports.all()[0]
        self.user_profile = self.user.userprofile
        self.mentor_profile = UserProfile.objects.get(
                user=self.user_profile.mentor)

    def test_send_email_on_add_report(self):
        """Test sending an email when a new report is added.
           Default option: True
        """
        self.new_report.save()
        eq_(len(mail.outbox), 1)

    def test_send_email_on_add_report_with_receive_mail_False(self):
        """Test sending an email when a new report is added
           and Mentor has the option in his/her settings disabled."""
        self.mentor_profile.receive_email_on_add_report = False
        self.mentor_profile.save()

        self.new_report.save()
        eq_(len(mail.outbox), 0)

    def test_send_email_on_edit_report_with_receive_mail_False(self):
        """Test sending an email when a report is edited.
           Default option: False
        """
        self.edit_report.save()
        eq_(len(mail.outbox), 0)

    def test_send_email_on_edit_report_with_receive_mail_True(self):
        """Test sending an email when a report is edited
           and Mentor has the option in his/her settings enabled.
        """
        self.mentor_profile.receive_email_on_edit_report = True
        self.mentor_profile.save()

        self.edit_report.save()
        eq_(len(mail.outbox), 1)


class UserNotificationOnAddComment(TestCase):
    """Test that a user receives an email when an authenticated user
    adds a comment on a report.
    """
    fixtures = ['demo_users.json', 'demo_reports.json']

    def setUp(self):
        self.date = datetime.datetime.now()
        self.user = User.objects.get(username='rep')
        self.user_profile = self.user.userprofile
        self.report = Report.objects.get(pk=1)
        self.commenter = self.user.userprofile.mentor
        self.new_comment = ReportComment(user=self.commenter,
                                         created_on=self.date,
                                         report=self.report)

    def test_send_email_on_add_comment_with_receive_mail_True(self):
        """Test sending email when a new comment is added.
        Default option: True
        """
        self.new_comment.save()
        eq_(len(mail.outbox), 1)

    def test_send_email_on_add_comment_with_receive_mail_False(self):
        """Test sending email when a new comment is added and
        user has the option disabled in his/her settings.
        """
        self.user_profile.receive_email_on_add_comment = False
        self.user_profile.save()

        self.new_comment.save()
        eq_(len(mail.outbox), 0)
