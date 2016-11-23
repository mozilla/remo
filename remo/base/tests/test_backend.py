from django.contrib.auth.models import User
from django.test import override_settings

import mock
from nose.tools import eq_

from remo.base.backend import RemoAuthenticationBackend
from remo.base.tests import RemoTestCase


class RemoBackendTests(RemoTestCase):
    """Test ReMo backend."""

    @override_settings(OIDC_OP_TOKEN_ENDPOINT='https://server.example.com/token')
    @override_settings(OIDC_OP_USER_ENDPOINT='https://server.example.com/userinfo')
    @override_settings(OIDC_RP_CLIENT_ID='client_id')
    @override_settings(OIDC_RP_CLIENT_SECRET='client_secret')
    @mock.patch('remo.base.backend.is_vouched')
    def test_create_mozillian_user_with_private_data(self, mocked_vouched):
        """ Test user creation for user with private data in Mozillians."""

        email = 'mozillian@example.com'

        eq_(User.objects.filter(email=email).count(), 0)

        backend = RemoAuthenticationBackend()
        backend.User = mock.Mock()
        mocked_vouched.return_value = {'is_vouched': True,
                                       'email': email}
        claims = {
            'foo': 'bar',
            'email': email
        }
        backend.create_user(claims)

        user = User.objects.get(email=email)
        eq_(user.get_full_name(), u'Anonymous Mozillian')

    @override_settings(OIDC_OP_TOKEN_ENDPOINT='https://server.example.com/token')
    @override_settings(OIDC_OP_USER_ENDPOINT='https://server.example.com/userinfo')
    @override_settings(OIDC_RP_CLIENT_ID='client_id')
    @override_settings(OIDC_RP_CLIENT_SECRET='client_secret')
    @mock.patch('remo.base.backend.is_vouched')
    def test_create_mozillian_user_with_public_name(self, mocked_vouched):
        """ Test user creation for user with private data in Mozillians."""

        email = 'mozillian@example.com'

        eq_(User.objects.filter(email=email).count(), 0)

        backend = RemoAuthenticationBackend()
        backend.User = mock.Mock()
        mocked_vouched.return_value = {'is_vouched': True,
                                       'email': email,
                                       'full_name': 'Awesome Mozillian',
                                       'username': 'remobot'}
        claims = {
            'foo': 'bar',
            'email': email
        }
        backend.create_user(claims)

        user = User.objects.get(email=email)
        eq_(user.get_full_name(), u'Awesome Mozillian')
