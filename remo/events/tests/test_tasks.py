from datetime import datetime, timedelta

from mock import call, patch
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.base.utils import get_date
from remo.events.tasks import notify_event_owners_to_input_metrics
from remo.events.tests import EventFactory
from remo.profiles.tests import UserFactory
from remo.reports import ACTIVITY_EVENT_CREATE
from remo.reports.tests import ActivityFactory


class SendEventNotificationsTests(RemoTestCase):

    def setUp(self):
        ActivityFactory.create(name=ACTIVITY_EVENT_CREATE)
        self.start = datetime.combine(get_date(days=-1), datetime.min.time())
        self.end = datetime.combine(get_date(days=-1), datetime.max.time())

    def test_base(self):
        owner = UserFactory.create()
        event = EventFactory.create(start=self.start, end=self.end, owner=owner)

        subject = ('[Reminder] Please add the actual metrics for event {0}'.format(event.name))
        template = 'email/event_creator_notification_to_input_metrics.jinja'

        with patch('remo.events.tasks.send_remo_mail.delay') as mail_mock:
            notify_event_owners_to_input_metrics()

        eq_(mail_mock.call_count, 1)
        expected_call_list = [call(subject=subject, recipients_list=[owner.id],
                                   email_template=template,
                                   data={'event': event})]
        eq_(mail_mock.call_args_list, expected_call_list)

    def test_end_date_in_the_future(self):
        owner = UserFactory.create()
        EventFactory.create(start=self.start, end=self.end + timedelta(days=2), owner=owner)

        with patch('remo.events.tasks.send_remo_mail.delay') as mail_mock:
            notify_event_owners_to_input_metrics()

        ok_(not mail_mock.called)

    def test_end_date_in_the_past(self):
        owner = UserFactory.create()
        EventFactory.create(start=self.start - timedelta(days=5),
                            end=self.end - timedelta(days=3), owner=owner)

        with patch('remo.events.tasks.send_remo_mail.delay') as mail_mock:
            notify_event_owners_to_input_metrics()

        ok_(not mail_mock.called)

    def test_with_existing_action_item(self):
        owner = UserFactory.create()
        EventFactory.create(start=self.start, end=self.end, owner=owner)

        with patch('remo.events.tasks.send_remo_mail.delay') as mail_mock:
            notify_event_owners_to_input_metrics()

        ok_(mail_mock.called)

        with patch('remo.events.tasks.send_remo_mail.delay') as mail_mock1:
            notify_event_owners_to_input_metrics()
        ok_(not mail_mock1.called)
