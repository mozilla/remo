from django.conf import settings

from mock import patch

from remo.base.tests import RemoTestCase
from remo.base.tasks import send_remo_mail
from remo.profiles.tests import UserFactory


class SendRemoMailTests(RemoTestCase):
    """Tests for the send_remo_mail task."""

    def test_base(self):
        recipient = UserFactory.create()
        sender = UserFactory.create()
        subject = 'This is the subject'
        message = 'This is the message'
        from_email = u'%s %s <%s>' % (sender.first_name,
                                      sender.last_name, sender.email)
        to = u'%s %s <%s>' % (recipient.first_name,
                              recipient.last_name, recipient.email)

        with patch('remo.base.tasks.EmailMessage') as mocked_email_message:
            send_remo_mail(subject, recipients_list=[recipient.id],
                           sender=from_email, message=message)

        mocked_email_message.assert_called_once_with(body=message,
                                                     to=[to],
                                                     cc=[from_email],
                                                     subject=subject,
                                                     headers={},
                                                     from_email=from_email)

    def test_send_email_from_remobot(self):
        recipient = UserFactory.create()
        subject = 'This is the subject'
        message = 'This is the message'
        to = u'%s %s <%s>' % (recipient.first_name,
                              recipient.last_name, recipient.email)

        with patch('remo.base.tasks.EmailMessage') as mocked_email_message:
            send_remo_mail(subject, recipients_list=[recipient.id],
                           message=message)

        mocked_email_message.assert_called_once_with(
            body=message, to=[to], subject=subject, headers={},
            from_email=settings.FROM_EMAIL)
