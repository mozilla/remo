from datetime import timedelta

from django.utils.timezone import now

from mock import call, patch
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.events.tasks import notify_event_owners_to_input_metrics
from remo.events.tests import EventFactory
from remo.profiles.tests import UserFactory


class SendEventNotificationsTests(RemoTestCase):
    def test_base(self):
        owner = UserFactory.create()
        end = now() - timedelta(days=1)
        event = EventFactory.create(end=end, owner=owner)

        subject = ('[Reminder] Please add the actual metrics for event {0}'
                   .format(event.name))
        template = 'email/event_creator_notification_to_input_metrics.txt'

        with patch('remo.events.tasks.send_remo_mail') as mail_mock:
            notify_event_owners_to_input_metrics()

        eq_(mail_mock.call_count, 1)
        expected_call_list = [call(subject=subject, recipients_list=[owner.id],
                                   email_template=template,
                                   data={'event': event})]
        eq_(mail_mock.call_args_list, expected_call_list)

    def test_end_date_in_the_future(self):
        owner = UserFactory.create()
        EventFactory.create(end=now() + timedelta(days=1),
                            owner=owner)

        with patch('remo.events.tasks.send_remo_mail') as mail_mock:
            notify_event_owners_to_input_metrics()

        ok_(not mail_mock.called)

    def test_end_date_in_the_past(self):
        owner = UserFactory.create()
        EventFactory.create(end=now() - timedelta(days=3),
                            owner=owner)

        with patch('remo.events.tasks.send_remo_mail') as mail_mock:
            notify_event_owners_to_input_metrics()

        ok_(not mail_mock.called)

    def test_with_existing_action_item(self):
        owner = UserFactory.create()
        end = now() - timedelta(days=1)
        EventFactory.create(end=end, owner=owner)

        with patch('remo.events.tasks.send_remo_mail') as mail_mock:
            notify_event_owners_to_input_metrics()

        ok_(mail_mock.called)

        with patch('remo.events.tasks.send_remo_mail') as mail_mock1:
            notify_event_owners_to_input_metrics()
        ok_(not mail_mock1.called)
