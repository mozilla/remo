from nose.tools import eq_, raises
from test_utils import TestCase
from django.test.client import Client

from remo.profiles.models import User

class ViewsTest(TestCase):
    fixtures = ['demo_users.json']

    def test_invite_user(self):
        c = Client()
        c.login(username="mentor", password="passwd")
        c.post('/people/invite/', {'email':'foobar@example.com'})

        u = User.objects.get(email="foobar@example.com")
        eq_(u.userprofile.added_by, User.objects.get(username="mentor"))


