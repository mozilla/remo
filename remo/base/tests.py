import base64

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.client import Client
from jinja2 import Markup
from nose.exc import SkipTest
from nose.tools import eq_
from test_utils import TestCase

from remo.base.helpers import AES_PADDING, enc_string, mailhide, pad_string
from remo.base.serializers import flatten_dict


class ViewsTest(TestCase):
    """Test views."""
    fixtures = ['demo_users.json']

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
        self.assertTemplateUsed(response, 'dashboard.html')

        # Get as logged in mentor.
        c.login(username='mentor', password='passwd')
        response = c.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

        # Get as logged in counselor.
        c.login(username='counselor', password='passwd')
        response = c.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_email_my_mentees_mentor(self):
        """Email mentees when mentor."""
        c = Client()
        c.login(username='mentor', password='passwd')
        data = {'subject': 'This is subject',
                'body': ('This is my body',
                         'Multiline ofcourse')}
        response = c.post(reverse('email_mentees'), data, follow=True)
        self.assertTemplateUsed(response, 'dashboard.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
        eq_(len(mail.outbox), 1)
        eq_(len(mail.outbox[0].to), 3)
        eq_(len(mail.outbox[0].cc), 1)

    def test_email_my_mentees_rep(self):
        """Email mentees when rep.

        Must fail since Rep doesn't have mentees."""
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


class TestSerializers(TestCase):
    """Test Serializers."""

    def test_dictionary_convertion(self):
        """Test flatten_dict()."""
        foobar = {'key1': 'value1',
                  'key2': {'skey1': 'svalue1'},
                  'key3': ['svalue2', 'svalue3']}

        expected_result = {'key1': 'value1',
                           'key2.skey1': 'svalue1',
                           'key3.0': 'svalue2',
                           'key3.1': 'svalue3'}

        eq_(flatten_dict(foobar), expected_result)
