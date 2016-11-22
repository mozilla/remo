# Authentication tests based on airmozilla
# https://github.com/mozilla/airmozilla/blob/master/airmozilla/\
#   auth/tests/test_views.py

import base64
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.test import RequestFactory
from django.test.client import Client
from django.test.utils import override_settings

import mock
from jinja2 import Markup
from nose.exc import SkipTest
from nose.tools import eq_, ok_

from remo.base import mozillians
from remo.base.templatetags.helpers import AES_PADDING, enc_string, mailhide, pad_string
from remo.base.tests import (MozillianResponse, RemoTestCase,
                             VOUCHED_MOZILLIAN, NOT_VOUCHED_MOZILLIAN,
                             requires_login, requires_permission)
from remo.base.views import robots_txt
from remo.profiles.models import FunctionalArea
from remo.profiles.tasks import check_mozillian_username
from remo.profiles.tests import (FunctionalAreaFactory, UserFactory,
                                 UserStatusFactory)
from remo.reports.models import Activity, Campaign
from remo.reports.tests import ActivityFactory, CampaignFactory


assert json.loads(VOUCHED_MOZILLIAN)
assert json.loads(NOT_VOUCHED_MOZILLIAN)


class MozilliansTest(RemoTestCase):
    """Test Moziilians."""

    @mock.patch('remo.base.mozillians.requests.get')
    @override_settings(MOZILLIANS_API_KEY='foo')
    @override_settings(MOZILLIANS_API_APPNAME='bar')
    def test_is_vouched(self, rget):
        """Test a user with vouched status"""

        def mocked_get(url, **options):
            if 'vouched' in url:
                return MozillianResponse(VOUCHED_MOZILLIAN)
            if 'not_vouched' in url:
                return MozillianResponse(NOT_VOUCHED_MOZILLIAN)
            if 'trouble' in url:
                return MozillianResponse('Failed', status_code=500)

        rget.side_effect = mocked_get

        ok_(mozillians.is_vouched('vouched@mail.com'))
        ok_(not mozillians.is_vouched('not_vouched@mail.com'))

        self.assertRaises(
            mozillians.BadStatusCodeError,
            mozillians.is_vouched,
            'trouble@live.com')

        try:
            mozillians.is_vouched('trouble@live.com')
            raise
        except mozillians.BadStatusCodeError, msg:
            ok_(settings.MOZILLIANS_API_KEY not in str(msg))

    @mock.patch('remo.profiles.tasks.is_vouched')
    def test_mozillian_username_exists(self, mocked_is_vouched):
        """Test that if an Anonymous Mozillians changes his

        settings in the mozillians.org, we update his username
        on our portal.
        """
        mozillian = UserFactory.create(groups=['Mozillians'])
        mocked_is_vouched.return_value = {'is_vouched': True,
                                          'email': mozillian.email,
                                          'username': 'Mozillian',
                                          'full_name': 'Awesome Mozillian'}
        check_mozillian_username.apply()
        user = User.objects.get(email=mozillian.email)
        eq_(user.userprofile.mozillian_username, u'Mozillian')
        eq_(user.get_full_name(), u'Awesome Mozillian')

    @mock.patch('remo.profiles.tasks.is_vouched')
    def test_mozillian_username_missing(self, mocked_is_vouched):
        """Test that if a Mozillian changes his

        settings in the mozillians.org, we update his username
        on our portal.
        """
        mozillian = UserFactory.create(
            groups=['Mozillians'], first_name='Awesome',
            last_name='Mozillian',
            userprofile__mozillian_username='Mozillian')
        mocked_is_vouched.return_value = {'is_vouched': True,
                                          'email': mozillian.email}
        check_mozillian_username.apply()
        user = User.objects.get(email=mozillian.email)
        eq_(user.userprofile.mozillian_username, '')
        eq_(user.get_full_name(), u'Anonymous Mozillian')


class ViewsTest(RemoTestCase):
    """Test views."""

    def setUp(self):
        self.settings_data = {'receive_email_on_add_comment': True}
        self.user_edit_settings_url = reverse('edit_settings')

    def test_view_main_page(self):
        """Get main page."""
        c = Client()
        response = c.get(reverse('main'))
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'main.jinja')

    def test_view_about_page(self):
        """Get about page."""
        c = Client()
        response = c.get(reverse('about'))
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'about.jinja')

    def test_view_faq_page(self):
        """Get faq page."""
        c = Client()
        response = c.get(reverse('faq'))
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'faq.jinja')

    def test_mailhide_encryption(self):
        """Test email encryption function."""
        if (getattr(settings, 'MAILHIDE_PUB_KEY', None) !=
                '01Ni54q--g1yltekhaSmPYHQ=='):
            raise SkipTest('Skipping test due to different MailHide pub key.')

        test_strings = [('foo@example.com', '3m5HgumLI4YSLSY-YP9HQA=='),
                        ('bar@example.net', '9o38o8PEvGrP6V5HSDg_FA=='),
                        ('test@mozilla.org', ('ABBkk5Aj2-PJ_izt9yU8pMzt'
                                              'wm-96eABHLBt8jRXxak='))]

        for string, encstring in test_strings:
            padded_string = pad_string(string, AES_PADDING)
            enced_string = enc_string(padded_string)
            safe_string = base64.urlsafe_b64encode(enced_string)
            eq_(encstring, safe_string)

    def test_mailhide_helper(self):
        """Test mailhide helper."""
        if (getattr(settings, 'MAILHIDE_PUB_KEY', None) !=
                '01Ni54q--g1yltekhaSmPYHQ=='):
            raise SkipTest('Skipping test due to different MailHide pub key.')

        m1 = Markup(u'<a href="http://mailhide.recaptcha.net/d?k=01Ni54q--g1yl'
                    'tekhaSmPYHQ==&c=3m5HgumLI4YSLSY-YP9HQA==" onclick="window'
                    '.open(\'http://mailhide.recaptcha.net/d?k=01Ni54q--g1ylte'
                    'khaSmPYHQ==&c=3m5HgumLI4YSLSY-YP9HQA==\', \'\', \'toolbar'
                    '=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizabl'
                    'e=0,width=500,height=300\'); return false;" title="Reveal'
                    ' this e-mail address">f...@example.com</a>')

        m2 = Markup(u'<a href="http://mailhide.recaptcha.net/d?k=01Ni54q--g1yl'
                    'tekhaSmPYHQ==&c=9o38o8PEvGrP6V5HSDg_FA==" onclick="window'
                    '.open(\'http://mailhide.recaptcha.net/d?k=01Ni54q--g1ylte'
                    'khaSmPYHQ==&c=9o38o8PEvGrP6V5HSDg_FA==\', \'\', \'toolbar'
                    '=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizabl'
                    'e=0,width=500,height=300\'); return false;" title="Reveal'
                    ' this e-mail address">b...@example.net</a>')

        m3 = Markup(u'<a href="http://mailhide.recaptcha.net/d?k=01Ni54q--g1yl'
                    'tekhaSmPYHQ==&c=ABBkk5Aj2-PJ_izt9yU8pMztwm-96eABHLBt8jRXx'
                    'ak=" onclick="window.open(\'http://mailhide.recaptcha.net'
                    '/d?k=01Ni54q--g1yltekhaSmPYHQ==&c=ABBkk5Aj2-PJ_izt9yU8pMz'
                    'twm-96eABHLBt8jRXxak=\', \'\', \'toolbar=0,scrollbars=0,l'
                    'ocation=0,statusbar=0,menubar=0,resizable=0,width=500,hei'
                    'ght=300\'); return false;" title="Reveal this e-mail addr'
                    'ess">t...@mozilla.org</a>')

        test_strings = [('foo@example.com', m1),
                        ('bar@example.net', m2),
                        ('test@mozilla.org', m3)]

        for string, markup in test_strings:
            eq_(mailhide(string), markup)

    @override_settings(ENGAGE_ROBOTS=True)
    def test_robots_allowed(self):
        """Test robots.txt generation when crawling allowed."""
        # Include a user who's not Rep
        UserFactory.create(userprofile__display_name='foo', groups=['Mozillian'])
        rep = UserFactory.create(groups=['Rep'])
        factory = RequestFactory()
        request = factory.get('/robots.txt')
        response = robots_txt(request)
        eq_(response.content,
            ('User-agent: *\nDisallow: /reports/\n'
             'Disallow: /u/{0}/r/\n'.format(rep.userprofile.display_name)))

    @override_settings(ENGAGE_ROBOTS=False)
    def test_robots_disallowed(self):
        """Test robots.txt generation when crawling disallowed."""
        factory = RequestFactory()
        request = factory.get('/robots.txt')
        response = robots_txt(request)
        eq_(response.content, 'User-agent: *\nDisallow: /\n')

    def test_view_edit_settings_page(self):
        """Get edit settings page."""
        c = Client()
        c.login(username='mentor', password='passwd')
        response = c.get(self.user_edit_settings_url)
        self.assertJinja2TemplateUsed(response, 'settings.jinja')

    def test_edit_settings_rep(self):
        """Test correct edit settings mail preferences as rep."""
        user = UserFactory.create()
        with self.login(user) as client:
            response = client.post(self.user_edit_settings_url,
                                   self.settings_data, follow=True)
        eq_(response.request['PATH_INFO'], reverse('dashboard'))

        # Ensure that settings data were saved
        user = User.objects.get(username=user.username)
        eq_(user.userprofile.receive_email_on_add_comment,
            self.settings_data['receive_email_on_add_comment'])


class TestContribute(RemoTestCase):

    def test_base(self):
        response = Client().get('/contribute.json')
        eq_(response.status_code, 200)
        # should be valid JSON
        ok_(json.loads(response.streaming_content.next()))
        eq_(response['Content-Type'], 'application/json')


class EditUserStatusTests(RemoTestCase):
    """Tests related to the User status edit View."""

    @requires_login()
    def test_get_as_anonymous(self):
        mentor = UserFactory.create()
        user = UserFactory.create(userprofile__mentor=mentor)
        display_name = user.userprofile.display_name
        UserStatusFactory.create(user=user)
        client = Client()
        client.get(reverse('edit_availability',
                           kwargs={'display_name': display_name}))

    def test_get_as_owner(self):
        mentor = UserFactory.create()
        user = UserFactory.create(userprofile__mentor=mentor)
        display_name = user.userprofile.display_name
        UserStatusFactory.create(user=user)
        url = reverse('edit_availability',
                      kwargs={'display_name': display_name})
        with self.login(user) as client:
            response = client.get(url, user=user)
        self.assertJinja2TemplateUsed(response, 'edit_availability.jinja')

    @requires_permission()
    def test_get_as_other_rep(self):
        mentor = UserFactory.create()
        user = UserFactory.create(userprofile__mentor=mentor)
        rep = UserFactory.create()
        display_name = user.userprofile.display_name
        UserStatusFactory.create(user=user)
        url = reverse('edit_availability',
                      kwargs={'display_name': display_name})
        with self.login(rep) as client:
            client.get(url, user=rep)

    @mock.patch('remo.base.views.messages.success')
    @mock.patch('remo.base.views.redirect', wraps=redirect)
    @mock.patch('remo.base.views.UserStatusForm')
    def test_add_unavailability_status(self, form_mock, redirect_mock,
                                       messages_mock):
        form_mock.is_valid.return_value = True
        user = UserFactory.create()
        display_name = user.userprofile.display_name
        with self.login(user) as client:
            response = client.post(reverse('edit_availability',
                                           kwargs={'display_name': display_name}),
                                   user=user, follow=True)
        eq_(response.status_code, 200)
        messages_mock.assert_called_with(
            mock.ANY, 'Request submitted successfully.')
        redirect_mock.assert_called_with('dashboard')
        ok_(form_mock().save.called)


class BaseListViewTest(RemoTestCase):
    """Test generic BaseListView class."""

    def test_base_content_activities_list(self):
        """Test list activities."""
        admin = UserFactory.create(groups=['Admin'])
        with self.login(admin) as client:
            response = client.get(reverse('list_activities'), follow=True)
        eq_(response.status_code, 200)
        eq_(response.context['verbose_name'], 'activity')
        eq_(response.context['verbose_name_plural'], 'activities')
        eq_(response.context['create_object_url'], reverse('create_activity'))
        self.assertJinja2TemplateUsed(response, 'base_content_list.jinja')

    def test_base_content_campaigns_list(self):
        """Test list campaigns."""
        admin = UserFactory.create(groups=['Admin'])
        with self.login(admin) as client:
            response = client.get(reverse('list_campaigns'), follow=True)
        eq_(response.status_code, 200)
        eq_(response.context['verbose_name'], 'initiative')
        eq_(response.context['verbose_name_plural'], 'initiatives')
        eq_(response.context['create_object_url'], reverse('create_campaign'))
        self.assertJinja2TemplateUsed(response, 'base_content_list.jinja')

    def test_base_content_functional_areas_list(self):
        """Test list functional areas."""
        admin = UserFactory.create(groups=['Admin'])
        with self.login(admin) as client:
            response = client.get(reverse('list_functional_areas'), follow=True)
        eq_(response.status_code, 200)
        eq_(response.context['verbose_name'], 'functional area')
        eq_(response.context['verbose_name_plural'], 'functional areas')
        eq_(response.context['create_object_url'],
            reverse('create_functional_area'))
        self.assertJinja2TemplateUsed(response, 'base_content_list.jinja')

    @requires_permission()
    def test_base_content_list_unauthed(self):
        """Test list base content unauthorized."""
        user = UserFactory.create(groups=['Rep'])
        with self.login(user) as client:
            client.get(reverse('list_activities'), follow=True)


class BaseCreateViewTest(RemoTestCase):
    """Test generic BaseCreateView class."""

    def test_base_content_activity_create_get(self):
        """Test get create activity."""
        admin = UserFactory.create(groups=['Admin'])
        with self.login(admin) as client:
            response = client.get(reverse('create_activity'), follow=True)
        eq_(response.status_code, 200)
        eq_(response.context['verbose_name'], 'activity')
        eq_(response.context['creating'], True)
        self.assertJinja2TemplateUsed(response, 'base_content_edit.jinja')

    def test_base_content_campaign_create_get(self):
        """Test get create campaign."""
        admin = UserFactory.create(groups=['Admin'])
        with self.login(admin) as client:
            response = client.get(reverse('create_campaign'), follow=True)
        eq_(response.status_code, 200)
        eq_(response.context['verbose_name'], 'initiative')
        eq_(response.context['creating'], True)
        self.assertJinja2TemplateUsed(response, 'base_content_edit.jinja')

    def test_base_content_functional_area_create_get(self):
        """Test get create functional area."""
        admin = UserFactory.create(groups=['Admin'])
        with self.login(admin) as client:
            response = client.get(reverse('create_functional_area'), follow=True)
        eq_(response.status_code, 200)
        eq_(response.context['verbose_name'], 'functional area')
        eq_(response.context['creating'], True)
        self.assertJinja2TemplateUsed(response, 'base_content_edit.jinja')

    def test_base_content_activity_create_post(self):
        """Test post create activity."""
        admin = UserFactory.create(groups=['Admin'])
        with self.login(admin) as client:
            response = client.post(reverse('create_activity'),
                                   data={'name': 'test activity'},
                                   follow=True)
        eq_(response.status_code, 200)
        query = Activity.objects.filter(name='test activity')
        eq_(query.exists(), True)

    def test_base_content_campaign_create_post(self):
        """Test post create campaign."""
        admin = UserFactory.create(groups=['Admin'])
        with self.login(admin) as client:
            response = client.post(reverse('create_campaign'),
                                   data={'name': 'test campaign'},
                                   follow=True)
        eq_(response.status_code, 200)
        query = Campaign.objects.filter(name='test campaign')
        eq_(query.exists(), True)

    def test_base_content_functional_area_create_post(self):
        """Test post create functional area."""
        admin = UserFactory.create(groups=['Admin'])
        with self.login(admin) as client:
            response = client.post(reverse('create_functional_area'),
                                   data={'name': 'test functional area'},
                                   follow=True)
        eq_(response.status_code, 200)
        query = FunctionalArea.objects.filter(name='test functional area')
        eq_(query.exists(), True)

    @requires_permission()
    def test_base_content_create_unauthed(self):
        """Test create base content unauthorized."""
        user = UserFactory.create(groups=['Rep'])
        with self.login(user) as client:
            client.post(reverse('create_functional_area'),
                        data={'name': 'test functional area'},
                        follow=True)


class BaseUpdateViewTest(RemoTestCase):
    """Test generic BaseUpdateView class."""

    def test_base_content_activity_edit_post(self):
        """Test post edit activity."""
        admin = UserFactory.create(groups=['Admin'])
        activity = ActivityFactory.create(name='test activity')
        with self.login(admin) as client:
            response = client.post(reverse('edit_activity', kwargs={'pk': activity.id}),
                                   data={'name': 'edit activity'},
                                   follow=True)
        eq_(response.status_code, 200)
        query = Activity.objects.filter(name='edit activity')
        eq_(query.exists(), True)

    def test_base_content_campaign_edit_post(self):
        """Test post edit campaign."""
        admin = UserFactory.create(groups=['Admin'])
        campaign = CampaignFactory.create(name='test campaign')
        with self.login(admin) as client:
            response = client.post(reverse('edit_campaign', kwargs={'pk': campaign.id}),
                                   data={'name': 'edit campaign'},
                                   follow=True)
        eq_(response.status_code, 200)
        query = Campaign.objects.filter(name='edit campaign')
        eq_(query.exists(), True)

    def test_base_content_functional_area_edit_post(self):
        """Test post edit functional area."""
        admin = UserFactory.create(groups=['Admin'])
        area = FunctionalAreaFactory.create(name='test functional area')
        with self.login(admin) as client:
            response = client.post(reverse('edit_functional_area',
                                           kwargs={'pk': area.id}),
                                   data={'name': 'edit functional area'},
                                   follow=True)
        eq_(response.status_code, 200)
        query = FunctionalArea.objects.filter(name='edit functional area')
        eq_(query.exists(), True)

    @requires_permission()
    def test_base_content_update_unauthed(self):
        """Test update base content unauthorized."""
        user = UserFactory.create(groups=['Rep'])
        campaign = CampaignFactory.create(name='test campaign')
        with self.login(user) as client:
            client.post(reverse('edit_campaign', kwargs={'pk': campaign.id}),
                        data={'name': 'edit campaign'},
                        follow=True)
