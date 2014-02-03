from datetime import date, datetime

from django.conf import settings

from mock import ANY as mockany, patch
from nose.tools import ok_

from remo.base.tests import RemoTestCase
from remo.events.tests import EventFactory
from remo.profiles.tests import UserFactory
from remo.reports import ACTIVITY_EVENT_ATTEND
from remo.reports.models import Activity, NGReport
from remo.reports.tasks import send_report_digest
from remo.reports.tests import NGReportFactory


class SendReportDigestTests(RemoTestCase):
    def test_base(self):
        mentor_1 = UserFactory.create(groups=['Mentor'])
        NGReportFactory.create_batch(2, mentor=mentor_1)
        NGReport.objects.update(created_on=date(2014, 1, 1))
        UserFactory.create(groups=['Mentor'])

        with patch('remo.reports.tasks.datetime') as datetime_mock:
            datetime_mock.utcnow().date.return_value = datetime(2014, 1, 1)
            with patch('remo.reports.tasks.send_mail') as send_mail_mock:
                with patch('remo.reports.tasks.DIGEST_SUBJECT', '{date}'):
                    send_report_digest()

        send_mail_mock.assert_called_with(
            'Wed 01 Jan 2014', mockany, settings.FROM_EMAIL, [mentor_1.email])

    def test_other_dates_noevent_not_included(self):
        """Reports created on previous days should not be included.

        Unless they are related to a today's event.

        """
        UserFactory.create(groups=['Mentor'])
        today = datetime.utcnow().date()
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
        today = datetime.utcnow().date()
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
