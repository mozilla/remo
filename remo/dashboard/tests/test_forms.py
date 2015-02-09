from django.contrib.auth.models import User
from django.core import mail
from django.test.client import RequestFactory

from mock import ANY, patch
from nose.tools import eq_, ok_
from test_utils import TestCase

from remo.dashboard.forms import EmailRepsForm
from remo.profiles.tests import FunctionalAreaFactory, UserFactory


class EmailRepsFormsTest(TestCase):

    def setUp(self):
        self.functional_area = FunctionalAreaFactory.create()

    def test_form_tampered_functional_area(self):
        """Test form with tampered data in functional area field."""
        data = {'subject': 'Test email subject',
                'body': None,
                'functional_area': 'Non existing functional area'}
        form = EmailRepsForm(data=data)
        ok_(not form.is_valid())
        eq_(len(form.errors['functional_area']), 1)

    @patch('remo.dashboard.forms.messages.success')
    def test_send_mail(self, fake_messages):
        """Test EmailRepsForm email sending functionality."""

        data = {'subject': 'Test email subject',
                'body': 'Test email body',
                'functional_area': self.functional_area.id}

        form = EmailRepsForm(data=data)
        ok_(form.is_valid())

        area = self.functional_area
        UserFactory.create_batch(20, userprofile__functional_areas=[area])

        factory = RequestFactory()
        request = factory.request()
        request.user = UserFactory.create()

        reps = User.objects.filter(userprofile__functional_areas__name=area)

        form.send_email(request, reps)

        eq_(len(mail.outbox), 20)

        def format_name(user):
            return '%s %s <%s>' % (user.first_name, user.last_name, user.email)
        recipients = map(format_name, reps)

        receivers = []
        for i in range(0, len(mail.outbox)):
            eq_(mail.outbox[i].subject, data['subject'])
            eq_(mail.outbox[i].body, data['body'])
            receivers.append(mail.outbox[i].to[0])

        eq_(set(receivers), set(recipients))
        fake_messages.assert_called_with(ANY, 'Email sent successfully.')
