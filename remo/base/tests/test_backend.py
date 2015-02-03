from django.contrib.auth.models import User

import mock
from nose.tools import eq_

from remo.base.backend import RemoBrowserIDBackend
from remo.base.tests import RemoTestCase


class RemoBackendTests(RemoTestCase):

    @mock.patch('remo.base.backend.is_vouched')
    def test_create_mozillian_user_with_private_data(self, mocked_vouched):
        """ Test user creation for user with private data in Mozillians."""

        email = 'mozillian@example.com'

        eq_(User.objects.filter(email=email).count(), 0)

        backend = RemoBrowserIDBackend()
        backend.User = mock.Mock()
        mocked_vouched.return_value = {'is_vouched': True,
                                       'email': email}
        backend.create_user(email)

        user = User.objects.get(email=email)
        eq_(user.get_full_name(), u'Anonymous Mozillian')

    @mock.patch('remo.base.backend.is_vouched')
    def test_create_mozillian_user_with_public_name(self, mocked_vouched):
        """ Test user creation for user with private data in Mozillians."""

        email = 'mozillian@example.com'

        eq_(User.objects.filter(email=email).count(), 0)

        backend = RemoBrowserIDBackend()
        backend.User = mock.Mock()
        mocked_vouched.return_value = {'is_vouched': True,
                                       'email': email,
                                       'full_name': 'Awesome Mozillian',
                                       'username': 'remobot'}
        backend.create_user(email)

        user = User.objects.get(email=email)
        eq_(user.get_full_name(), u'Awesome Mozillian')
