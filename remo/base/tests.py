from django.core.urlresolvers import reverse
from django.test.client import Client
from nose.tools import eq_
from test_utils import TestCase


class ViewsTest(TestCase):
    """Test views."""

    def test_view_main_page(self):
        """Get main page."""
        c = Client()
        response = c.get(reverse('main'))
        eq_(response.status_code, 200)
