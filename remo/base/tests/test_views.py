# Authentication tests based on airmozilla
# https://github.com/mozilla/airmozilla/blob/master/airmozilla/\
#   auth/tests/test_views.py

import base64
import json
import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.test.client import Client
from django.test.utils import override_settings

from funfactory.helpers import urlparams
from jinja2 import Markup
from nose.exc import SkipTest
from nose.tools import eq_, ok_
from test_utils import TestCase

from remo.base import mozillians
from remo.base.helpers import AES_PADDING, enc_string, mailhide, pad_string
from remo.base.tests.browserid_mock import mock_browserid
from remo.base.views import robots_txt


VOUCHED_MOZILLIAN = """
{
    "meta": {
        "previous": null,
        "total_count": 1,
        "offset": 0,
        "limit": 20,
        "next": null
    },
    "objects":
    [
        {
            "website": "",
            "bio": "",
            "groups": [
                "foo bar"
            ],
            "skills": [],
            "email": "vouched@mail.com",
            "is_vouched": true
        }
    ]
}
"""

NOT_VOUCHED_MOZILLIAN = """
{
  "meta": {
    "previous": null,
    "total_count": 1,
    "offset": 0,
    "limit": 20,
    "next": null
  },
  "objects": [
    {
      "website": "",
      "bio": "",
      "groups": [
        "no login"
      ],
      "skills": [],
      "is_vouched": false,
      "email": "not_vouched@mail.com"
    }
  ]
}
"""


assert json.loads(VOUCHED_MOZILLIAN)
assert json.loads(NOT_VOUCHED_MOZILLIAN)


class MozillianResponse(object):
    """Mozillians Response."""

    def __init__(self, content=None, status_code=200):
        self.content = content
        self.status_code = status_code


class MozilliansTest(TestCase):
    """Test Moziilians."""

    @mock.patch('requests.get')
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

    @override_settings(SITE_URL='http://testserver')
    @mock.patch('remo.base.views.verify')
    @mock.patch('remo.base.views.is_vouched')
    @mock.patch('remo.base.views.auth.authenticate')
    def test_mozillian_user_with_private_data(self, mocked_authenticate,
                                              mocked_is_vouched,
                                              mocked_verify):
        """ Test user creation for user with private data in Mozillians."""
        c = Client()
        email = u'vouched@example.com'
        mocked_verify.return_value = {'email': email}
        mocked_is_vouched.return_value = {'is_vouched': True,
                                          'email': email}

        def authenticate(*args, **kwargs):
            user = User.objects.get(email=email)
            user.backend = 'Fake'
            return user

        mocked_authenticate.side_effect = authenticate
        eq_(User.objects.filter(email=email).count(), 0)
        c.post('/browserid/login/', data={'assertion': 'xxx'})
        user = User.objects.get(email=email)
        eq_(user.get_full_name(), u'Anonymous Mozillian')


class ViewsTest(TestCase):
    """Test views."""
    fixtures = ['demo_users.json']

    def setUp(self):
        self.settings_data = {'receive_email_on_add_report': False,
                              'receive_email_on_edit_report': True,
                              'receive_email_on_add_comment': True}
        self.user_edit_settings_url = reverse('edit_settings')
        self.failed_url = urlparams(settings.LOGIN_REDIRECT_URL_FAILURE,
                                    bid_login_failed=1)

    def _login_attempt(self, email, assertion='assertion123'):
        with mock_browserid(email):
            r = self.client.post(
                reverse('browserid_login'),
                {'assertion': assertion})
        return r

    def test_bad_verification(self):
        """Bad verification -> failure."""
        response = self._login_attempt(None)
        self.assertRedirects(response, self.failed_url,
                             target_status_code=200)

    def test_invalid_login(self):
        """Bad BrowserID form - no assertion -> failure."""
        response = self._login_attempt(None, None)
        self.assertRedirects(response, self.failed_url,
                             target_status_code=200)

    def test_is_vouched(self):
        """Login with vouched email."""
        response = self._login_attempt('vouched@mail.com')
        eq_(response.status_code, 302)
        ok_(reverse('dashboard'))

    def test_view_main_page(self):
        """Get main page."""
        c = Client()
        response = c.get(reverse('main'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')

    def test_view_dashboard_page(self):
        """Get dashboard page."""
        c = Client()

        # Get as anonymous user.
        response = c.get(reverse('dashboard'), follow=True)
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')

        # Get as logged in rep.
        c.login(username='rep', password='passwd')
        response = c.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_reps.html')

        # Get as logged in mentor.
        c.login(username='mentor', password='passwd')
        response = c.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_reps.html')

        # Get as logged in counselor.
        c.login(username='counselor', password='passwd')
        response = c.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_reps.html')

    def test_email_my_mentees_mentor_with_send_True(self):
        """Email mentees when mentor and checkbox
        is checked."""
        c = Client()
        c.login(username='mentor', password='passwd')
        rep1 = User.objects.get(first_name='Nick')
        data = {'%s %s <%s>' % (rep1.first_name,
                                rep1.last_name,
                                rep1.email): 'True',
                'subject': 'This is subject',
                'body': ('This is my body\n',
                         'Multiline of course')}
        response = c.post(reverse('email_mentees'), data, follow=True)
        self.assertTemplateUsed(response, 'dashboard_reps.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
        eq_(len(mail.outbox), 1)
        eq_(len(mail.outbox[0].to), 1)
        eq_(len(mail.outbox[0].cc), 1)

    def test_email_my_mentees_mentor_with_send_False(self):
        """Email mentees when mentor and checkbox is
        not checked."""
        c = Client()
        c.login(username='mentor', password='passwd')
        rep1 = User.objects.get(first_name='Nick')
        data = {'%s %s <%s>' % (rep1.first_name,
                                rep1.last_name,
                                rep1.email): 'False',
                'subject': 'This is subject',
                'body': ('This is my body\n',
                         'Multiline of course')}
        response = c.post(reverse('email_mentees'), data, follow=True)
        self.assertTemplateUsed(response, 'dashboard_reps.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')
        eq_(len(mail.outbox), 0)

    def test_email_my_mentees_rep(self):
        """Email mentees when rep.

        Must fail since Rep doesn't have mentees.
        """
        c = Client()
        c.login(username='rep', password='passwd')
        data = {'subject': 'This is subject',
                'body': ('This is my body',
                         'Multiline ofcourse')}
        response = c.post(reverse('email_mentees'), data, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')
        eq_(len(mail.outbox), 0)

    def test_email_reps_as_mozillian(self):
        """Email all the reps associated with a functional area."""

        c = Client()
        c.login(username='mozillian1', password='passwd')
        data = {'subject': 'This is subject',
                'body': 'This is my body\n Multiline of course',
                'functional_area': 2}
        response = c.post(reverse('dashboard'), data, follow=True)
        self.assertTemplateUsed(response, 'dashboard_mozillians.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
        eq_(len(mail.outbox), 1)

    def test_view_about_page(self):
        """Get about page."""
        c = Client()
        response = c.get(reverse('about'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')

    def test_view_faq_page(self):
        """Get faq page."""
        c = Client()
        response = c.get(reverse('faq'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'faq.html')

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

    def test_view_edit_settings_page(self):
        """Get edit settings page."""
        c = Client()
        c.login(username='mentor', password='passwd')
        response = c.get(self.user_edit_settings_url)
        self.assertTemplateUsed(response, 'settings.html')

    def test_edit_settings_mentor(self):
        """Test correct edit settings mail preferences as mentor."""
        c = Client()
        c.login(username='mentor', password='passwd')
        response = c.post(self.user_edit_settings_url,
                          self.settings_data, follow=True)
        eq_(response.request['PATH_INFO'], reverse('dashboard'))

        # Ensure that settings data were saved
        user = User.objects.get(username='mentor')
        eq_(user.userprofile.receive_email_on_add_report,
            self.settings_data['receive_email_on_add_report'])
        eq_(user.userprofile.receive_email_on_edit_report,
            self.settings_data['receive_email_on_edit_report'])

    def test_edit_settings_rep(self):
        """Test correct edit settings mail preferences as rep."""
        c = Client()
        c.login(username='rep', password='passwd')
        response = c.post(self.user_edit_settings_url,
                          self.settings_data, follow=True)
        eq_(response.request['PATH_INFO'], reverse('dashboard'))

        # Ensure that settings data were saved
        user = User.objects.get(username='rep')
        eq_(user.userprofile.receive_email_on_add_comment,
            self.settings_data['receive_email_on_add_comment'])

    @override_settings(ENGAGE_ROBOTS=True)
    def test_robots_allowed(self):
        """Test robots.txt generation when crawling allowed."""
        factory = RequestFactory()
        request = factory.get('/robots.txt')
        response = robots_txt(request)
        eq_(response.content, 'User-agent: *\nAllow: /')

    @override_settings(ENGAGE_ROBOTS=False)
    def test_robots_disallowed(self):
        """Test robots.txt generation when crawling disallowed."""
        factory = RequestFactory()
        request = factory.get('/robots.txt')
        response = robots_txt(request)
        eq_(response.content, 'User-agent: *\nDisallow: /')
