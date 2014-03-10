import datetime

from django.contrib.auth.models import User
from django.core import mail
from nose.tools import eq_, ok_
from test_utils import TestCase

import fudge
import mock

from remo.base.utils import go_back_n_months
from remo.events.helpers import get_event_link
from remo.events.tests import EventFactory, AttendanceFactory
from remo.profiles.tests import UserFactory
from remo.reports import ACTIVITY_EVENT_ATTEND, ACTIVITY_EVENT_CREATE
from remo.reports.models import Activity, NGReport, OVERDUE_DAY
from remo.reports.tests import (NGReportFactory, NGReportCommentFactory,
                                NGReportCommentFactoryNoSignals,
                                ReportCommentFactory, ReportFactory)


class ModelTest(TestCase):
    """Tests related to Reports Models."""

    def setUp(self):
        """Setup tests."""
        self.new_mentor = UserFactory.create(username='mentor',
                                             groups=['Mentor'])
        self.user_mentor = UserFactory.create(username='counselor',
                                              groups=['Mentor'])
        self.user = UserFactory.create(username='rep', groups=['Rep'],
                                       userprofile__mentor=self.user_mentor)
        self.month_year = datetime.date(year=2012, month=1, day=10)
        self.report = ReportFactory.create(user=self.user,
                                           month=self.month_year,
                                           mentor=self.user.userprofile.mentor)

    def test_mentor_set_for_new_report(self):
        """Test that report mentor field stays the same when user

           changes mentor.
        """
        eq_(self.report.mentor, self.user.userprofile.mentor)

        # Change user mentor and re-save the report. Report should
        # point to the first mentor.
        self.user.userprofile.mentor = self.new_mentor
        self.user.save()

        self.report.save()
        eq_(self.report.mentor, self.user_mentor)

    def test_overdue_true(self):
        """Test overdue report (first test)."""
        ok_(self.report.overdue)

    @fudge.patch('datetime.date.today')
    def test_overdue_true_2(self, fake_requests_obj):
        """Test overdue report (second test)."""
        today = datetime.datetime.today()

        # act like it's OVERDUE_DAY + 1
        fake_date = datetime.datetime(year=today.year, month=today.month,
                                      day=OVERDUE_DAY + 1)
        (fake_requests_obj.expects_call().returns(fake_date))

        month_year = go_back_n_months(today)
        report = ReportFactory.create(user=self.user, month=month_year)
        ok_(report.overdue)

    def test_overdue_false(self):
        """Test not overdue report (first test)."""
        # Change report created_on, so report is not overdue
        month_year = datetime.date(year=2020, month=1, day=10)
        report = ReportFactory.create(user=self.user, month=month_year)
        ok_(not report.overdue)

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
        report = ReportFactory.create(user=self.user, month=month_year)
        ok_(not report.overdue)

    def test_set_month_day(self):
        """Test that reports month always points to first day of the month."""
        eq_(self.report.month.day, 1)


class MentorNotificationOnAddEditReport(TestCase):
    """Test that a Mentor receives an email when a Mentee

        adds/edits a report.
    """

    def setUp(self):
        self.date = datetime.datetime.now()
        self.mentor = UserFactory.create(username='counselor',
                                         groups=['Mentor'])
        self.user = UserFactory.create(username='rep', groups=['Rep'],
                                       userprofile__mentor=self.mentor)
        self.month_year = datetime.date(year=2012, month=1, day=10)
        self.new_report = ReportFactory.build(
            user=self.user, month=self.date,
            mentor=self.user.userprofile.mentor)
        self.mentor_profile = self.mentor.userprofile

    def test_send_email_on_add_report(self):
        """Test sending an email when a new report is added.

           Default option: True
        """
        self.new_report.save()
        eq_(len(mail.outbox), 1)

    def test_send_email_on_add_report_with_receive_mail_False(self):
        """Test sending an email when a new report is added

           and Mentor has the option in his/her settings disabled.
        """
        self.mentor_profile.receive_email_on_add_report = False
        self.mentor_profile.save()

        self.new_report.save()
        eq_(len(mail.outbox), 0)

    def test_send_email_on_edit_report_with_receive_mail_False(self):
        """Test sending an email when a report is edited.

           Default option: False
        """
        self.mentor_profile.receive_email_on_edit_report = False
        self.mentor_profile.receive_email_on_add_report = False
        self.mentor_profile.save()

        ReportFactory.create(user=self.user, mentor=self.mentor)
        eq_(len(mail.outbox), 0)

    def test_send_email_on_edit_report_with_receive_mail_True(self):
        """Test sending an email when a report is edited

           and Mentor has the option in his/her settings enabled.
        """
        self.mentor_profile.receive_email_on_edit_report = True
        self.mentor_profile.save()

        ReportFactory.create(user=self.user, mentor=self.mentor)
        eq_(len(mail.outbox), 1)


class UserNotificationOnAddComment(TestCase):
    """Test that a user receives an email when an authenticated user

    adds a comment on a report.
    """

    def setUp(self):
        self.date = datetime.datetime.now()
        self.mentor = UserFactory.create(
            username='counselor', groups=['Mentor'],
            userprofile__receive_email_on_add_report=False)
        self.user = UserFactory.create(username='rep', groups=['Rep'],
                                       userprofile__mentor=self.mentor)
        self.user_profile = self.user.userprofile
        self.report = ReportFactory.create(user=self.user,
                                           month=self.date,
                                           mentor=self.user.userprofile.mentor)
        self.new_comment = ReportCommentFactory.build(user=self.mentor,
                                                      created_on=self.date,
                                                      report=self.report)
        self.month_year = datetime.date(year=2012, month=1, day=10)

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


class NGReportTest(TestCase):
    def test_get_absolute_url(self):
        report = NGReportFactory.create(
            report_date=datetime.date(2012, 01, 01), id=9999)
        eq_(report.get_absolute_url(),
            ('/u/%s/r/2012/January/1/9999/'
             % report.user.userprofile.display_name))

    def test_get_absolute_edit_url(self):
        report = NGReportFactory.create(
            report_date=datetime.date(2012, 01, 01), id=9999)
        eq_(report.get_absolute_edit_url(),
            ('/u/%s/r/2012/January/1/9999/edit/'
             % report.user.userprofile.display_name))

    def test_get_absolute_delete_url(self):
        report = NGReportFactory.create(
            report_date=datetime.date(2012, 01, 01), id=9999)
        eq_(report.get_absolute_delete_url(),
            ('/u/%s/r/2012/January/1/9999/delete/'
             % report.user.userprofile.display_name))

    def test_current_longest_streak(self):
        today = datetime.datetime.utcnow().date()
        user = UserFactory.create()

        for i in range(0, 2):
            NGReportFactory.create(
                user=user, report_date=today - datetime.timedelta(days=i))

        eq_(user.userprofile.current_streak_start,
            today - datetime.timedelta(days=1))
        eq_(user.userprofile.longest_streak_start,
            today - datetime.timedelta(days=1))
        eq_(user.userprofile.longest_streak_end, today)

    def test_different_current_longest_streak(self):
        today = datetime.datetime.utcnow().date()
        past_day = (datetime.datetime.utcnow().date() -
                    datetime.timedelta(days=30))
        user = UserFactory.create()
        #longest streak
        for i in range(0, 3):
            NGReportFactory.create(
                user=user, report_date=past_day - datetime.timedelta(days=i))

        # current streak
        for i in range(0, 2):
            NGReportFactory.create(
                user=user, report_date=today - datetime.timedelta(days=i))

        eq_(user.userprofile.current_streak_start,
            today - datetime.timedelta(days=1))
        eq_(user.userprofile.longest_streak_start,
            past_day - datetime.timedelta(days=2))
        eq_(user.userprofile.longest_streak_end, past_day)

    def test_current_streak_counter_with_past_reports(self):
        past_day = (datetime.datetime.utcnow().date() -
                    datetime.timedelta(days=30))

        user = UserFactory.create()
        for i in range(0, 5):
            NGReportFactory.create(
                user=user, report_date=past_day - datetime.timedelta(days=i))

        ok_(not user.userprofile.current_streak_start)


class NGReportComment(TestCase):
    def test_get_absolute_delete_url(self):
        report = NGReportFactory.create(
            report_date=datetime.date(2012, 01, 01), id=9999)
        report_comment = NGReportCommentFactory.create(report=report,
                                                       user=report.user)
        eq_(report_comment.get_absolute_delete_url(),
            ('/u/%s/r/2012/January/1/9999/comment/%s/delete/'
             % (report.user.userprofile.display_name, report_comment.id)))


class NGReportAttendanceSignalTests(TestCase):
    def test_owner(self):
        """Test creating a passive attendance report for event owner."""
        activity = Activity.objects.get(name=ACTIVITY_EVENT_ATTEND)
        user = UserFactory.create(groups=['Rep', 'Mentor'],
                                  userprofile__initial_council=True)
        event = EventFactory.create(owner=user)
        report = NGReport.objects.get(event=event, user=user,
                                      activity=activity)

        location = '%s, %s, %s' % (event.city, event.region, event.country)
        eq_(report.mentor, user.userprofile.mentor)
        eq_(report.activity.name, ACTIVITY_EVENT_ATTEND)
        eq_(report.latitude, event.lat)
        eq_(report.longitude, event.lon)
        eq_(report.location, location)
        eq_(report.is_passive, True)
        eq_(report.link, get_event_link(event))
        eq_(report.activity_description, event.description)
        self.assertQuerysetEqual(report.functional_areas.all(),
                                 [e.name for e in event.categories.all()],
                                 lambda x: x.name)

    def test_attendee(self):
        """Test creating a passive report after attending an event."""
        activity = Activity.objects.get(name=ACTIVITY_EVENT_ATTEND)
        event = EventFactory.create()
        user = UserFactory.create(groups=['Rep', 'Mentor'],
                                  userprofile__initial_council=True)
        AttendanceFactory.create(event=event, user=user)
        report = NGReport.objects.get(event=event, user=user,
                                      activity=activity)

        location = '%s, %s, %s' % (event.city, event.region, event.country)
        eq_(report.mentor, user.userprofile.mentor)
        eq_(report.activity.name, ACTIVITY_EVENT_ATTEND)
        eq_(report.latitude, event.lat)
        eq_(report.longitude, event.lon)
        eq_(report.location, location)
        eq_(report.is_passive, True)
        eq_(report.link, get_event_link(event))
        eq_(report.activity_description, event.description)
        self.assertQuerysetEqual(report.functional_areas.all(),
                                 [e.name for e in event.categories.all()],
                                 lambda x: x.name)

    def test_delete_attendance(self):
        """Test delete passive report after attendance delete."""
        activity = Activity.objects.get(name=ACTIVITY_EVENT_ATTEND)
        event = EventFactory.create()
        user = UserFactory.create(groups=['Rep', 'Mentor'],
                                  userprofile__initial_council=True)
        attendance = AttendanceFactory.create(event=event, user=user)
        ok_(NGReport.objects.filter(event=event, user=user).exists())
        attendance.delete()
        query = NGReport.objects.filter(event=event, user=user,
                                        activity=activity)
        ok_(not query.exists())


class NGReportEventCreationSignalTests(TestCase):

    def test_create(self):
        """Test creating a passive report after creating an event."""
        activity = Activity.objects.get(name=ACTIVITY_EVENT_CREATE)
        event = EventFactory.build()
        event.owner = UserFactory.create()
        event.save()
        report = NGReport.objects.get(event=event, user=event.owner,
                                      activity=activity)

        location = '%s, %s, %s' % (event.city, event.region, event.country)
        eq_(report.mentor, event.owner.userprofile.mentor)
        eq_(report.activity.name, ACTIVITY_EVENT_CREATE)
        eq_(report.latitude, event.lat)
        eq_(report.longitude, event.lon)
        eq_(report.location, location)
        eq_(report.is_passive, True)
        eq_(report.link, get_event_link(event))
        eq_(report.activity_description, event.description)
        self.assertQuerysetEqual(report.functional_areas.all(),
                                 [e.name for e in event.categories.all()],
                                 lambda x: x.name)

    def test_delete(self):
        """Test delete passive report after event delete."""
        activity = Activity.objects.get(name=ACTIVITY_EVENT_CREATE)
        event = EventFactory.create()
        user = event.owner
        query = NGReport.objects.filter(event=event, user=user,
                                        activity=activity)
        ok_(query.exists())
        event.delete()

        query = NGReport.objects.filter(event=event, user=user,
                                        activity=activity)
        ok_(not query.exists())

    def test_update(self):
        """Test update report after event edit."""
        event = EventFactory.create()
        report = NGReportFactory.create(user=event.owner, event=event,
                                        report_date=event.start.date())
        eq_(report.report_date, event.start.date())

        event.start += datetime.timedelta(days=5)
        event.end += datetime.timedelta(days=5)
        event.save()
        report = NGReport.objects.get(pk=report.id)
        eq_(report.report_date.day, event.start.day)

    def test_edit_owner(self):
        """Test change event ownership."""
        owner = UserFactory.create()
        event = EventFactory.build(owner=owner)
        event.save()
        report = NGReport.objects.get(user=owner)
        new_owner = UserFactory.create()
        report.event.owner = new_owner
        report.event.save()
        report = NGReport.objects.get(pk=report.id)
        eq_(report.user, new_owner)
        eq_(report.mentor, new_owner.userprofile.mentor)

    def test_edit_functional_areas(self):
        """Test update report after changes in event's functional areas."""
        event = EventFactory.create()
        categories = event.categories.all()
        report = NGReportFactory.create(user=event.owner, event=event,
                                        functional_areas=categories)

        event.categories = categories[:1]
        report = NGReport.objects.get(pk=report.id)
        self.assertQuerysetEqual(report.functional_areas.all(),
                                 [e.name for e in categories.all()[:1]],
                                 lambda x: x.name)


class NGReportCommentSignalTests(TestCase):
    def test_comment_one_user(self):
        """Test sending email when a new comment is added on a NGReport
        and the user has the option enabled in his/her settings.
        """
        commenter = UserFactory.create()
        reporter = UserFactory.create(
            userprofile__receive_email_on_add_comment=True)
        report = NGReportFactory.create(user=reporter)
        NGReportCommentFactory.create(user=commenter, report=report,
                                      comment='This is a comment')

        eq_(len(mail.outbox), 1)
        eq_(reporter.email, mail.outbox[0].to[0])
        msg = ('[Report] User {0} commented on {1}'
               .format(commenter.get_full_name(), report))
        eq_(mail.outbox[0].subject, msg)

    def test_one_user_settings_False(self):
        """Test sending email when a new comment is added on a NGReport
        and the user has the option disabled in his/her settings.
        """
        comment_user = UserFactory.create()
        user = UserFactory.create(
            userprofile__receive_email_on_add_comment=False)
        report = NGReportFactory.create(user=user)
        NGReportCommentFactory.create(user=comment_user, report=report,
                                      comment='This is a comment')

        eq_(len(mail.outbox), 0)

    def test_comment_multiple_users(self):
        """Test sending email when a new comment is added on a NGReport
        and the users have the option enabled in their settings.
        """
        commenter = UserFactory.create()
        reporter = UserFactory.create(
            userprofile__receive_email_on_add_comment=True)
        report = NGReportFactory.create(user=reporter)
        users_with_comments = UserFactory.create_batch(
            2, userprofile__receive_email_on_add_comment=True)
        # disconnect the signals in order to add two users in NGReportComment
        for user_obj in users_with_comments:
            NGReportCommentFactoryNoSignals.create(
                user=user_obj, report=report, comment='This is a comment')
        NGReportCommentFactory.create(user=commenter, report=report,
                                      comment='This is a comment')

        eq_(len(mail.outbox), 3)
        recipients = [reporter.email, users_with_comments[0].email,
                      users_with_comments[1].email]
        receivers = [mail.outbox[0].to[0], mail.outbox[1].to[0],
                     mail.outbox[2].to[0]]
        eq_(set(recipients), set(receivers))
        msg = ('[Report] User {0} commented on {1}'
               .format(commenter.get_full_name(), report))
        eq_(mail.outbox[0].subject, msg)


class NGReportDeleteSignalTests(TestCase):

    def test_current_streak_oldest_report(self):
        """Update current and longest streak counters when the oldest
        report out of two is deleted.
        """

        user = UserFactory.create()
        up = user.userprofile
        today = datetime.datetime.utcnow().date()
        report = NGReportFactory.create(
            user=user, report_date=today - datetime.timedelta(days=1))
        NGReportFactory.create(user=user, report_date=today)
        eq_(up.current_streak_start, today - datetime.timedelta(days=1))
        eq_(up.longest_streak_start, today - datetime.timedelta(days=1))
        eq_(up.longest_streak_end, today)

        report.delete()

        eq_(up.current_streak_start, today)
        eq_(up.longest_streak_start, today)
        eq_(up.longest_streak_end, today)

    def test_current_streak_latest_report(self):
        """Update current and longest streak counters when the latest
        report out of two is deleted.
        """

        user = UserFactory.create()
        up = user.userprofile
        today = datetime.datetime.utcnow().date()
        NGReportFactory.create(user=user,
                               report_date=today - datetime.timedelta(days=1))
        report = NGReportFactory.create(user=user, report_date=today)
        eq_(up.current_streak_start, today - datetime.timedelta(days=1))
        eq_(up.longest_streak_start, today - datetime.timedelta(days=1))
        eq_(up.longest_streak_end, today)

        report.delete()

        eq_(up.current_streak_start, today - datetime.timedelta(days=1))
        eq_(up.longest_streak_start, today - datetime.timedelta(days=1))
        eq_(up.longest_streak_end, today - datetime.timedelta(days=1))

    def test_delete_all(self):
        """Update current and longest streak when all reports are deleted."""

        user = UserFactory.create()
        up = user.userprofile
        today = datetime.datetime.utcnow().date()
        report1 = NGReportFactory.create(
            user=user, report_date=today - datetime.timedelta(days=1))
        report2 = NGReportFactory.create(user=user, report_date=today)
        eq_(up.current_streak_start, today - datetime.timedelta(days=1))
        eq_(up.longest_streak_start, today - datetime.timedelta(days=1))
        eq_(up.longest_streak_end, today)

        report1.delete()
        report2.delete()

        ok_(not up.current_streak_start)
        ok_(not up.longest_streak_start)
        ok_(not up.longest_streak_end)

    @mock.patch('remo.reports.models.get_date')
    def test_longest_streak(self, mocked_date):
        """Update current and longest streak counters when the fourth
        report out of five is deleted.
        """

        mocked_date.return_value = datetime.date(2011, 01, 29)
        user = UserFactory.create()
        up = user.userprofile
        start_date = datetime.date(2011, 01, 01)
        end_date = datetime.date(2011, 01, 29)
        # Create 5 reports
        for i in range(0, 5):
            NGReportFactory.create(
                user=user,
                report_date=end_date - datetime.timedelta(weeks=i))

        eq_(up.current_streak_start, start_date)
        eq_(up.longest_streak_start, start_date)
        eq_(up.longest_streak_end, end_date)

        # Delete the report that the user submitted on 22-01-2012
        NGReport.objects.filter(
            user=user,
            report_date=datetime.date(2011, 01, 22)).delete()

        user = User.objects.get(pk=user.id)
        up = user.userprofile
        eq_(up.current_streak_start, end_date)
        eq_(up.longest_streak_start, start_date)
        eq_(up.longest_streak_end, datetime.date(2011, 01, 15))
