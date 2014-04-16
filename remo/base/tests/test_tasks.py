from django.conf import settings

from mock import patch
from nose.tools import ok_

from remo.base.tests import RemoTestCase
from remo.base.tasks import send_remo_mail
from remo.profiles.tests import UserFactory


class SendRemoMailTests(RemoTestCase):
    """Tests for the send_remo_mail task."""

    def test_base(self):
        recipient = UserFactory.create()
        subject = 'This is the subject'
        message = 'This is the message'
        from_email = u'Joe Doe <joe@example.com>'
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

    def test_without_message_and_template(self):
        recipient = UserFactory.create()
        subject = 'This is the subject'
        from_email = u'Joe Doe <joe@example.com>'

        with patch('remo.base.tasks.EmailMessage') as mocked_email_message:
            send_remo_mail(subject, recipients_list=[recipient.id],
                           sender=from_email,)
        ok_(not mocked_email_message.called)

    def test_without_recipients(self):
        subject = 'This is the subject'
        message = 'This is the message'
        from_email = u'Joe Doe <joe@example.com>'

        with patch('remo.base.tasks.EmailMessage') as mocked_email_message:
            send_remo_mail(subject, sender=from_email, message=message,
                           recipients_list=None)
        ok_(not mocked_email_message.called)

    def test_send_to_valid_email_address(self):
        subject = 'This is the subject'
        message = 'This is the message'
        from_email = u'Joe Doe <joe@example.com>'

        with patch('remo.base.tasks.EmailMessage') as mocked_email_message:
            send_remo_mail(subject, recipients_list=['mail@example.com'],
                           sender=from_email, message=message)

        mocked_email_message.assert_called_once_with(body=message,
                                                     to=['mail@example.com'],
                                                     cc=[from_email],
                                                     subject=subject,
                                                     headers={},
                                                     from_email=from_email)

    def test_send_to_invalid_email_address(self):
        subject = 'This is the subject'
        message = 'This is the message'
        from_email = u'Joe Doe <joe@example.com>'

        with patch('remo.base.tasks.EmailMessage') as mocked_email_message:
            send_remo_mail(subject, recipients_list=['Not an address'],
                           sender=from_email, message=message)
        ok_(not mocked_email_message.called)

    def test_headers(self):
        subject = 'This is the subject'
        message = 'This is the message'
        from_email = u'Joe Doe <joe@example.com>'
        headers = {'Reply-To': 'mail@example.com'}

        with patch('remo.base.tasks.EmailMessage') as mocked_email_message:
            send_remo_mail(subject, recipients_list=['mail@example.com'],
                           sender=from_email, message=message, headers=headers)

        mocked_email_message.assert_called_once_with(body=message,
                                                     to=['mail@example.com'],
                                                     cc=[from_email],
                                                     subject=subject,
                                                     from_email=from_email,
                                                     headers=headers)
