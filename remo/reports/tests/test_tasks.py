from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import now

from mock import ANY as mockany, call, patch
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.base.utils import get_date
from remo.events.tests import EventFactory
from remo.profiles.tests import UserFactory
from remo.reports import ACTIVITY_EVENT_ATTEND
from remo.reports.models import Activity, NGReport
from remo.reports.tasks import (calculate_longest_streaks,
                                send_first_report_notification,
                                send_second_report_notification,
                                send_report_digest,
                                zero_current_streak)
from remo.reports.tests import NGReportFactory


class SendReportDigestTests(RemoTestCase):
    def test_base(self):
        mentor = UserFactory.create(groups=['Mentor'])
        report_1 = NGReportFactory.create(
            mentor=mentor, report_date=date(2013, 11, 1))
        report_2 = NGReportFactory.create(
            mentor=mentor, report_date=date(2014, 1, 1))
        NGReport.objects.update(created_on=date(2014, 1, 1))

        with patch('remo.reports.tasks.now') as datetime_now:
            datetime_now.return_value = datetime(2014, 1, 1)
            with patch('remo.reports.tasks.render_to_string') as render_mock:
                render_mock.return_value = 'rendered'
                with patch('remo.reports.tasks.send_mail') as send_mail_mock:
                    with patch('remo.reports.tasks.DIGEST_SUBJECT', '{date}'):
                        send_report_digest()

        call_args = render_mock.call_args[0]
        eq_(call_args[1]['mentor'], mentor)
        eq_(set(call_args[1]['reports']), set([report_1, report_2]))
        eq_(call_args[1]['datestring'], 'Wed 01 Jan 2014')

        send_mail_mock.assert_called_with(
            'Wed 01 Jan 2014', 'rendered', settings.FROM_EMAIL, [mentor.email])

    def test_other_dates_noevent_not_included(self):
        """Reports created on previous days should not be included.

        Unless they are related to a today's event.

        """
        UserFactory.create(groups=['Mentor'])
        today = now().date()
        # Report is not related to event attedance or creation.
        report = NGReportFactory.create(report_date=today)
        report.created_on = date(2014, 01, 01)
        report.save()
        with patch('remo.reports.tasks.send_mail') as send_mail_mock:
            send_report_digest()
        ok_(not send_mail_mock.called)

    def test_other_dates_event_included(self):
        """Reports for today's events should be included."""
        UserFactory.create(groups=['Mentor'])
        today = now().date()
        mentor = UserFactory.create(groups=['Mentor'])
        activity, created = Activity.objects.get_or_create(
            name=ACTIVITY_EVENT_ATTEND)
        event = EventFactory.create()
        report = NGReportFactory.create(report_date=today,
                                        activity=activity,
                                        event=event,
                                        mentor=mentor)
        report.created_on = date(2014, 01, 01)
        report.save()
        with patch('remo.reports.tasks.send_mail') as send_mail_mock:
            send_report_digest()
        ok_(send_mail_mock.called)


class SendInactivityNotifications(RemoTestCase):
    def test_base(self):
        mentor = UserFactory.create(groups=['Mentor'])
        today = now().date()
        rep = UserFactory.create(
            groups=['Rep'], userprofile__mentor=mentor,
            userprofile__date_joined_program=get_date(days=-100))
        NGReportFactory.create(user=rep,
                               report_date=today - timedelta(weeks=5))

        rep_subject = '[Reminder] Please share your recent activities'
        mentor_subject = '[Report] Mentee without report for the last 4 weeks'

        with patch('remo.reports.utils.send_remo_mail') as mail_mock:
            send_first_report_notification()

        eq_(mail_mock.call_count, 2)
        expected_call_list = [
            call(rep_subject, [rep.email], message=mockany,
                 headers={'Reply-To': mentor.email}),
            call(mentor_subject, [mentor.email], message=mockany,
                 headers={'Reply-To': rep.email})]
        eq_(mail_mock.call_args_list, expected_call_list)

    def test_with_report_filled(self):
        mentor = UserFactory.create(groups=['Mentor'])
        today = now().date()
        rep = UserFactory.create(
            groups=['Rep'], userprofile__mentor=mentor)
        NGReportFactory.create(user=rep,
                               report_date=today - timedelta(weeks=2))

        with patch('remo.reports.utils.send_remo_mail') as mail_mock:
            send_second_report_notification()
        ok_(not mail_mock.called)

    def test_with_no_report_filled_and_one_notification(self):
        mentor = UserFactory.create(groups=['Mentor'])
        today = now().date()
        rep = UserFactory.create(
            groups=['Rep'], userprofile__mentor=mentor,
            userprofile__first_report_notification=today - timedelta(weeks=4))
        NGReportFactory.create(user=rep,
                               report_date=today - timedelta(weeks=9))

        rep_subject = '[Reminder] Please share your recent activities'
        mentor_subject = '[Report] Mentee without report for the last 8 weeks'

        with patch('remo.reports.utils.send_remo_mail') as mail_mock:
            send_second_report_notification()

        eq_(mail_mock.call_count, 2)
        expected_call_list = [
            call(rep_subject, [rep.email], message=mockany,
                 headers={'Reply-To': mentor.email}),
            call(mentor_subject, [mentor.email], message=mockany,
                 headers={'Reply-To': rep.email})]
        eq_(mail_mock.call_args_list, expected_call_list)

    def test_with_user_unavailable(self):
        mentor = UserFactory.create(groups=['Mentor'])
        today = now().date()
        rep = UserFactory.create(
            groups=['Rep'], userprofile__mentor=mentor,
            userprofile__date_joined_program=get_date(days=-100),
            userprofile__is_unavailable=True)
        NGReportFactory.create(user=rep,
                               report_date=today - timedelta(weeks=5))

        with patch('remo.reports.utils.send_remo_mail') as mail_mock:
            send_first_report_notification()

        ok_(not mail_mock.called)


class UpdateCurrentStreakCountersTest(RemoTestCase):
    def test_base(self):
        past_day = get_date(-8)
        user = UserFactory.create(groups=['Rep'])
        NGReportFactory.create(user=user, report_date=past_day)
        user.userprofile.current_streak_start = past_day
        user.userprofile.save()

        zero_current_streak()
        user = User.objects.get(pk=user.id)

        ok_(not user.userprofile.current_streak_start)


class UpdateStreakCountersTaskTest(RemoTestCase):
    def test_no_current_streak(self):
        user = UserFactory.create(groups=['Rep'])
        for i in range(4):
            report_date = date(2011, 01, 01) + timedelta(weeks=i)
            NGReportFactory.create(user=user, report_date=report_date)

        calculate_longest_streaks()
        eq_(user.userprofile.longest_streak_start, date(2011, 01, 01))
        eq_(user.userprofile.longest_streak_end, date(2011, 01, 22))

    def test_with_smaller_current_streak(self):
        user = UserFactory.create(groups=['Rep'])
        for i in range(3):
            report_date = date.today() - timedelta(weeks=i)
            NGReportFactory.create(user=user, report_date=report_date)

        eq_(user.userprofile.longest_streak_start,
            date.today() - timedelta(weeks=2))
        eq_(user.userprofile.longest_streak_end, date.today())

        for i in range(4):
            report_date = date(2011, 01, 01) + timedelta(weeks=i)
            NGReportFactory.create(user=user, report_date=report_date)

        calculate_longest_streaks()

        user = User.objects.get(pk=user.id)
        eq_(user.userprofile.longest_streak_start, date(2011, 01, 01))
        eq_(user.userprofile.longest_streak_end, date(2011, 01, 22))

    def test_with_larger_current_streak(self):
        user = UserFactory.create(groups=['Rep'])
        for i in range(4):
            report_date = date.today() - timedelta(weeks=i)
            NGReportFactory.create(user=user, report_date=report_date)

        eq_(user.userprofile.longest_streak_start,
            date.today() - timedelta(weeks=3))
        eq_(user.userprofile.longest_streak_end, date.today())

        for i in range(3):
            report_date = date(2011, 01, 01) + timedelta(weeks=i)
            NGReportFactory.create(user=user, report_date=report_date)

        calculate_longest_streaks()

        user = User.objects.get(pk=user.id)
        eq_(user.userprofile.longest_streak_start,
            date.today() - timedelta(weeks=3))
        eq_(user.userprofile.longest_streak_end, date.today())
