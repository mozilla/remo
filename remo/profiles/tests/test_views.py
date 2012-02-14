from nose.tools import eq_
from django.test.client import Client
from test_utils import TestCase

from remo.profiles.models import User


class ViewsTest(TestCase):
    fixtures = ['demo_users.json']

    def test_invite_user(self):
        c = Client()
        c.login(username="mentor", password="passwd")
        c.post('/people/invite/', {'email': 'foobar@example.com'})

        u = User.objects.get(email="foobar@example.com")
        eq_(u.userprofile.added_by, User.objects.get(username="mentor"))

    def test_edit_profile_permissions(self):
        # user edits own profile
        c = Client()
        c.login(username="rep", password="passwd")
        response = c.get('/u/koki/edit/', follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

        # admin edits user's profile
        c = Client()
        c.login(username="admin", password="passwd")
        response = c.get('/u/koki/edit/', follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

        # third user denied permission to edit user's profile
        c = Client()
        c.login(username="mentor", password="passwd")
        response = c.get('/u/koki/edit/', follow=True)
        self.assertTemplateUsed(response, 'main.html')

    def test_delete_profile(self):
        # user can't delete own profile
        c = Client()
        c.login(username="rep", password="passwd")
        response = c.post('/u/koki/delete/', follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # admin can delete user's profile
        c = Client()
        c.login(username="admin", password="passwd")
        response = c.post('/u/koki/delete/', {'delete': 'true'}, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')

        # third user can't delete user's profile
        c = Client()
        c.login(username="mentor", password="passwd")
        response = c.post('/u/koki/delete/', follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

    def test_profiles_me(self):
        # user gets own profile page rendered
        c = Client()
        c.login(username="rep", password="passwd")
        response = c.get('/people/me/', follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html')

        # anonymous user get message to login first
        c = Client()
        response = c.get('/people/me/', follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')

    def test_uncomplete_profile(self):
        c = Client()
        c.login(username="rep2", password="passwd")
        response = c.get('/people/me/', follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')
