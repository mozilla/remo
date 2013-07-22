from django.contrib.auth.models import User
from django.core import mail
from django.test.client import RequestFactory
from nose.tools import eq_, ok_
from test_utils import TestCase

import fudge

from remo.base.forms import EmailRepsForm
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

    @fudge.patch('remo.base.forms.messages')
    def test_send_mail(self, fake_messages):
        """Test EmailRepsForm email sending functionality."""

        fake_messages.expects('success')

        data = {'subject': 'Test email subject',
                'body': 'Test email body',
                'functional_area': self.functional_area}

        form = EmailRepsForm(data=data)
        ok_(form.is_valid())

        area = self.functional_area
        UserFactory.create_batch(20, userprofile__functional_areas=[area])

        factory = RequestFactory()
        request = factory.request()
        request.user = UserFactory.create()

        reps = User.objects.filter(userprofile__functional_areas__name=area)

        form.send_email(request, reps)

        eq_(len(mail.outbox), 1)

        address = lambda u: '%s %s <%s>' % (u.first_name, u.last_name, u.email)
        recipients = map(address, reps)

        eq_(set(mail.outbox[0].to), set(recipients))
        eq_(mail.outbox[0].subject, data['subject'])
        eq_(mail.outbox[0].body, data['body'])
