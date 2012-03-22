from django.core.urlresolvers import reverse
from django.test.client import Client
from nose.tools import eq_
from test_utils import TestCase


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

        # Get as logged in user.
        c.login(username='rep', password='passwd')
        response = c.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

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
