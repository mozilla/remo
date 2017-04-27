from contextlib import contextmanager, nested

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.test import TestCase as BaseTestCase
from django.test.client import Client
from django.test.utils import override_settings

from django_jinja.backend import Template as Jinja_Template
from mock import patch
from nose.tools import make_decorator, ok_


AUTHENTICATION_BACKENDS = (
    'remo.base.tests.authentication.DummyAuthenticationBackend',
)

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
)


@override_settings(AUTHENTICATION_BACKENDS=AUTHENTICATION_BACKENDS,
                   PASSWORD_HASHERS=PASSWORD_HASHERS)
class RemoTestCase(BaseTestCase):

    @contextmanager
    def login(self, user):
        client = Client()
        client.login(email=user.email)
        yield client

    def assertJinja2TemplateUsed(self, response, template_name, **kwargs):
        for template in response.templates:
            if isinstance(template, Jinja_Template):
                self.assertEqual(template.template.name, template_name)
                break


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
