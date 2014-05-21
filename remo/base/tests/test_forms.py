from django.contrib.auth.models import User
from django.core import mail
from django.test.client import RequestFactory

from mock import ANY, patch
from nose.tools import eq_, ok_
from test_utils import TestCase

from remo.base.forms import EmailRepsForm, EmailUsersForm
from remo.profiles.tests import FunctionalAreaFactory, UserFactory


class EmailRepsFormsTest(TestCase):

    def test_form_tampered_functional_area(self):
        """Test form with tampered data in functional area field."""
        data = {'subject': 'Test email subject',
                'body': None,
                'functional_area': 'Non existing functional area'}
        form = EmailRepsForm(data=data)
        ok_(not form.is_valid())
        eq_(len(form.errors['functional_area']), 1)

    @patch('remo.base.forms.messages.success')
    def test_send_mail(self, fake_messages):
        """Test EmailRepsForm email sending functionality."""
        functional_area = FunctionalAreaFactory.create()

        data = {'subject': 'Test email subject',
                'body': 'Test email body',
                'functional_area': functional_area.id}

        form = EmailRepsForm(data=data)
        ok_(form.is_valid())

        users = UserFactory.create_batch(
            20, userprofile__functional_areas=[functional_area])

        factory = RequestFactory()
        request = factory.request()
        request.user = UserFactory.create()

        reps = User.objects.filter(
            userprofile__functional_areas__name=functional_area)

        form.send_email(request, reps)

        eq_(len(mail.outbox), 1)

        address = lambda u: '%s %s <%s>' % (u.first_name, u.last_name, u.email)
        recipients = map(address, reps)
        receivers = map(address, users)

        eq_(mail.outbox[0].subject, data['subject'])
        eq_(mail.outbox[0].body, data['body'])
        eq_(set(receivers), set(recipients))
        fake_messages.assert_called_with(ANY, 'Email sent successfully.')


class EmailUsersFormTest(TestCase):

    @patch('remo.base.forms.messages.success')
    def test_base(self, fake_messages):
        """Test EmailUsersForm email sending functionality."""

        data = {'subject': 'Test email subject',
                'body': 'Test email body'}

        mentor = UserFactory.create(groups=['Mentor'])
        users = UserFactory.create_batch(5, userprofile__mentor=mentor)

        factory = RequestFactory()
        request = factory.request()
        request.user = mentor

        mentees = User.objects.filter(userprofile__mentor=mentor)
        for mentee in mentees:
            mentee_id = '{mentee_id}'.format(mentee_id=mentee.id)
            data[mentee_id] = True
        form = EmailUsersForm(mentees, data=data)
        ok_(form.is_valid())

        form.send_mail(request)

        address = lambda u: '%s %s <%s>' % (u.first_name, u.last_name, u.email)
        recipients = map(address, mentees)
        receivers = map(address, users)

        eq_(len(mail.outbox), 1)
        eq_(mail.outbox[0].subject, data['subject'])
        eq_(mail.outbox[0].body, data['body'])
        eq_(set(receivers), set(recipients))
        cc_recipient = ['%s %s <%s>' % (mentor.first_name, mentor.last_name,
                                        mentor.email)]
        eq_(set(mail.outbox[0].recipients()), set(recipients + cc_recipient))
        fake_messages.assert_called_with(ANY, 'Email sent successfully.')
