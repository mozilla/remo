from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.test.client import Client

import mock
from mock import patch
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase, requires_permission
from remo.featuredrep.models import FeaturedRep
from remo.featuredrep.tests import FeaturedRepFactory
from remo.profiles.tests import UserFactory


class ViewsTest(RemoTestCase):

    def test_get_as_admin(self):
        user = UserFactory.create(groups=['Admin'])
        featured = FeaturedRepFactory.create()
        with self.login(user) as client:
            response = client.get(reverse('featuredrep_edit_featured', args=[featured.id]))
        self.assertJinja2TemplateUsed(response, 'featuredrep_alter.jinja')

    def test_get_as_council(self):
        user = UserFactory.create(groups=['Council'])
        featured = FeaturedRepFactory.create()
        with self.login(user) as client:
            response = client.get(reverse('featuredrep_edit_featured', args=[featured.id]))
        self.assertJinja2TemplateUsed(response, 'featuredrep_alter.jinja')

    @requires_permission()
    def test_get_as_other_user(self):
        user = UserFactory.create()
        featured = FeaturedRepFactory.create()
        with self.login(user) as client:
            client.get(reverse('featuredrep_edit_featured', args=[featured.id]), follow=True)

    def test_get_list_featured_page(self):
        """Get list featuredrep page."""
        UserFactory.create(groups=['Admin'])
        FeaturedRepFactory.create_batch(3)
        response = Client().get(reverse('featuredrep_list_featured'))
        self.assertJinja2TemplateUsed(response, 'featuredrep_list.jinja')

    @patch('remo.featuredrep.views.messages.success')
    @patch('remo.featuredrep.views.redirect', wraps=redirect)
    @patch('remo.featuredrep.views.forms.FeaturedRepForm')
    def test_add_new_featured(self, form_mock, redirect_mock, messages_mock):
        form_mock.is_valid.return_value = True
        user = UserFactory.create(groups=['Admin'])
        with self.login(user) as client:
            response = client.post(reverse('featuredrep_add_featured'), follow=True)
        eq_(response.status_code, 200)
        messages_mock.assert_called_with(mock.ANY, 'New featured rep article created.')
        ok_(form_mock().save.called)

    @patch('remo.featuredrep.views.messages.success')
    @patch('remo.featuredrep.views.redirect', wraps=redirect)
    @patch('remo.featuredrep.views.forms.FeaturedRepForm')
    def test_edit_featured(self, form_mock, redirect_mock, messages_mock):
        form_mock.is_valid.return_value = True
        featured = FeaturedRepFactory.create()
        user = UserFactory.create(groups=['Admin'])
        with self.login(user) as client:
            response = client.post(reverse('featuredrep_edit_featured', args=[featured.id]),
                                   user=user, follow=True)
        eq_(response.status_code, 200)
        messages_mock.assert_called_with(
            mock.ANY, 'Featured rep article successfuly edited.')
        ok_(form_mock().save.called)

    @patch('remo.featuredrep.views.redirect', wraps=redirect)
    def test_delete_featured(self, redirect_mock):
        user = UserFactory.create(groups=['Admin'])
        featured = FeaturedRepFactory.create()
        with self.login(user) as client:
            client.post(reverse('featuredrep_delete_featured', args=[featured.id]))
        ok_(not FeaturedRep.objects.filter(pk=featured.id).exists())
