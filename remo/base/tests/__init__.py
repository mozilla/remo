from contextlib import nested

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.test.client import Client
from django.test.utils import override_settings

from mock import patch
from nose.tools import make_decorator, ok_
from test_utils import TestCase as BaseTestCase


AUTHENTICATION_BACKENDS = (
    'remo.base.tests.authentication.DummyAuthenticationBackend',
    )


@override_settings(AUTHENTICATION_BACKENDS=AUTHENTICATION_BACKENDS)
class RemoTestCase(BaseTestCase):
    def get(self, url, data={}, user=None, follow=True):
        client = Client()
        if user:
            client.login(email=user.email)
        return client.get(url, data, follow=follow)

    def post(self, url, data={}, user=None, follow=True):
        client = Client()
        if user:
            client.login(email=user.email)
        return client.post(url, data, follow=follow)


def requires_login():
    def decorate(func):
        def newfunc(*args, **kwargs):
            with patch(
                    'remo.base.decorators.messages.warning') as messages_mock:
                with patch('remo.base.decorators.HttpResponseRedirect',
                           wraps=HttpResponseRedirect) as redirect_mock:
                    func(*args, **kwargs)
            ok_(messages_mock.called, 'messages.warning() was not called.')
            ok_(redirect_mock.called)
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate


def requires_permission():
    def decorate(func):
        def newfunc(*args, **kwargs):
            with nested(
                    patch('remo.base.decorators.messages.error'),
                    patch('remo.base.decorators.redirect',
                          wraps=redirect)) as (messages_mock, redirect_mock):
                func(*args, **kwargs)
            ok_(messages_mock.called, 'messages.error() was not called.')
            redirect_mock.assert_called_with('main')
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate
