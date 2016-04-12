import datetime

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.utils.timezone import now

import mock
from factory.django import mute_signals
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.events.templatetags.helpers import get_event_link
from remo.events.tests import EventFactory, AttendanceFactory
from remo.profiles.tests import UserFactory
from remo.reports import ACTIVITY_EVENT_ATTEND, ACTIVITY_EVENT_CREATE
from remo.reports.models import Activity, NGReport
from remo.reports.tests import ActivityFactory, NGReportFactory, NGReportCommentFactory


class NGReportTest(RemoTestCase):
    def test_get_absolute_url(self):
        report = NGReportFactory.create(
            report_date=datetime.date(2012, 01, 01), id=9999)
        eq_(report.get_absolute_url(),
            '/u/{0}/r/2012/January/1/9999/'.format(report.user.userprofile.display_name))

    def test_get_absolute_edit_url(self):
        report = NGReportFactory.create(
            report_date=datetime.date(2012, 01, 01), id=9999)
        eq_(report.get_absolute_edit_url(),
            '/u/{0}/r/2012/January/1/9999/edit/'.format(report.user.userprofile.display_name))

    def test_get_absolute_delete_url(self):
        report = NGReportFactory.create(
            report_date=datetime.date(2012, 01, 01), id=9999)
        eq_(report.get_absolute_delete_url(),
            '/u/{0}/r/2012/January/1/9999/delete/'.format(report.user.userprofile.display_name))

    def test_current_longest_streak(self):
        today = now().date()
        user = UserFactory.create()

        for i in range(0, 2):
            NGReportFactory.create(user=user, report_date=today - datetime.timedelta(days=i))

        eq_(user.userprofile.current_streak_start, today - datetime.timedelta(days=1))
        eq_(user.userprofile.longest_streak_start, today - datetime.timedelta(days=1))
        eq_(user.userprofile.longest_streak_end, today)

    def test_different_current_longest_streak(self):
        today = now().date()
        past_day = now().date() - datetime.timedelta(days=30)
        user = UserFactory.create()
        # longest streak
        for i in range(0, 3):
            NGReportFactory.create(user=user, report_date=past_day - datetime.timedelta(days=i))

        # current streak
        for i in range(0, 2):
            NGReportFactory.create(user=user, report_date=today - datetime.timedelta(days=i))

        eq_(user.userprofile.current_streak_start, today - datetime.timedelta(days=1))
        eq_(user.userprofile.longest_streak_start, past_day - datetime.timedelta(days=2))
        eq_(user.userprofile.longest_streak_end, past_day)

    def test_current_streak_counter_with_past_reports(self):
        past_day = now().date() - datetime.timedelta(days=30)

        user = UserFactory.create()
        for i in range(0, 5):
            NGReportFactory.create(user=user, report_date=past_day - datetime.timedelta(days=i))

        ok_(not user.userprofile.current_streak_start)


class NGReportComment(RemoTestCase):
    def test_get_absolute_delete_url(self):
        report = NGReportFactory.create(report_date=datetime.date(2012, 01, 01), id=9999)
        report_comment = NGReportCommentFactory.create(report=report, user=report.user)
        eq_(report_comment.get_absolute_delete_url(),
            '/u/{0}/r/2012/January/1/9999/comment/{1}/delete/'.format(
                report.user.userprofile.display_name, report_comment.id))


class NGReportAttendanceSignalTests(RemoTestCase):

    def setUp(self):
        ActivityFactory.create(name=ACTIVITY_EVENT_ATTEND)
        ActivityFactory.create(name=ACTIVITY_EVENT_CREATE)

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


class NGReportEventCreationSignalTests(RemoTestCase):

    def setUp(self):
        ActivityFactory.create(name=ACTIVITY_EVENT_ATTEND)
        ActivityFactory.create(name=ACTIVITY_EVENT_CREATE)

    def test_create(self):
        """Test creating a passive report after creating an event."""
        activity = Activity.objects.get(name=ACTIVITY_EVENT_CREATE)
        owner = UserFactory.create()
        event = EventFactory.create(owner=owner)
        report = NGReport.objects.get(event=event, user=event.owner, activity=activity)

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
        report = NGReport.objects.get(user=event.owner, event=event)
        eq_(report.report_date, event.start.date())

        event.start += datetime.timedelta(days=5)
        event.end += datetime.timedelta(days=5)
        event.save()
        report = NGReport.objects.get(pk=report.id)
        eq_(report.report_date.day, event.start.day)

    def test_edit_owner(self):
        """Test change event ownership."""
        owner = UserFactory.create()
        EventFactory.create(owner=owner)
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


class NGReportCommentSignalTests(RemoTestCase):

    @mock.patch('remo.reports.models.send_remo_mail.delay')
    def test_comment_one_user(self, mocked_mail):
        """Test sending email when a new comment is added on a NGReport
        and the user has the option enabled in his/her settings.
        """
        commenter = UserFactory.create()
        reporter = UserFactory.create(userprofile__receive_email_on_add_comment=True)
        report = NGReportFactory.create(user=reporter)
        NGReportCommentFactory.create(user=commenter, report=report, comment='This is a comment')

        ok_(mocked_mail.called)
        eq_(mocked_mail.call_count, 1)
        mocked_data = mocked_mail.call_args_list[0][1]
        msg = '[Report] User {0} commented on {1}'.format(commenter.get_full_name(), report)
        eq_(mocked_data['subject'], msg)

    @mock.patch('remo.reports.models.send_remo_mail.delay')
    def test_one_user_settings_False(self, mocked_mail):
        """Test sending email when a new comment is added on a NGReport
        and the user has the option disabled in his/her settings.
        """
        comment_user = UserFactory.create()
        user = UserFactory.create(
            userprofile__receive_email_on_add_comment=False)
        report = NGReportFactory.create(user=user)
        NGReportCommentFactory.create(user=comment_user, report=report,
                                      comment='This is a comment')
        ok_(not mocked_mail.called)

    @mock.patch('remo.reports.models.send_remo_mail.delay')
    def test_comment_multiple_users(self, mocked_mail):
        """Test sending email when a new comment is added on a NGReport
        and the users have the option enabled in their settings.
        """
        commenter = UserFactory.create()
        reporter = UserFactory.create(userprofile__receive_email_on_add_comment=True)
        report = NGReportFactory.create(user=reporter)
        users_with_comments = UserFactory.create_batch(
            2, userprofile__receive_email_on_add_comment=True)
        # disconnect the signals in order to add two users in NGReportComment
        with mute_signals(post_save):
            for user_obj in users_with_comments:
                NGReportCommentFactory.create(user=user_obj, report=report,
                                              comment='This is a comment')
        NGReportCommentFactory.create(user=commenter, report=report,
                                      comment='This is a comment')

        ok_(mocked_mail.called)
        eq_(mocked_mail.call_count, 3)
        msg = '[Report] User {0} commented on {1}'.format(commenter.get_full_name(), report)
        mocked_data = mocked_mail.call_args_list[0][1]
        eq_(mocked_data['subject'], msg)


class NGReportDeleteSignalTests(RemoTestCase):

    def test_current_streak_oldest_report(self):
        """Update current and longest streak counters when the oldest
        report out of two is deleted.
        """

        user = UserFactory.create()
        up = user.userprofile
        today = now().date()
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
        today = now().date()
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
        today = now().date()
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


class NGReportActivityNotifications(RemoTestCase):
    def test_user_new_activity(self):
        report_notification = now().date() - datetime.timedelta(weeks=3)
        new_report_date = now().date() + datetime.timedelta(weeks=1)

        rep = UserFactory.create(
            groups=['Rep'],
            userprofile__first_report_notification=report_notification
        )
        NGReportFactory.create(user=rep, report_date=new_report_date)

        user = User.objects.get(pk=rep.id)
        ok_(not user.userprofile.first_report_notification)
        ok_(not user.userprofile.second_report_notification)

    def test_user_new_future_activity(self):
        report_notification = now().date() - datetime.timedelta(weeks=3)
        new_report_date = now().date() + datetime.timedelta(weeks=6)

        rep = UserFactory.create(
            groups=['Rep'],
            userprofile__first_report_notification=report_notification
        )
        NGReportFactory.create(user=rep, report_date=new_report_date)

        user = User.objects.get(pk=rep.id)
        eq_(user.userprofile.first_report_notification, report_notification)
