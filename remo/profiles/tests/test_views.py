import datetime
import time

from django.core.urlresolvers import reverse
from django.test.client import Client
from nose.tools import eq_
from test_utils import TestCase

from pyquery import PyQuery as pq

from remo.profiles.models import User


class ViewsTest(TestCase):
    """Tests related to Profiles Views."""
    fixtures = ['demo_users.json',
                'demo_bugs.json']

    def setUp(self):
        """Setup tests."""
        self.data = {'display_name': u'Koki',
                     'first_name': u'first',
                     'email': u'rep@example.com',
                     'last_name': u'last',
                     'local_name': u'local',
                     'birth_date': u'1980-01-01',
                     'private_email': u'private_email@bar.com',
                     'twitter_account': u'foobar',
                     'city': u'city',
                     'region': u'region',
                     'country': u'Greece',
                     'lon': 12.23,
                     'lat': 12.23,
                     'mozillians_profile_url': u'http://mozillians.org/',
                     'wiki_profile_url': u'https://wiki.mozilla.org/User:',
                     'jabber_id': u'foo@jabber.org',
                     'irc_name': u'ircname',
                     'linkedin_url': u'http://www.linkedin.com/',
                     'facebook_url': u'http://www.facebook.com/',
                     'diaspora_url': u'https://joindiaspora.com/',
                     'personal_website_url': u'http://www.example.com/',
                     'personal_blog_feed': u'http://example.com/',
                     'bio': u'bio foo',
                     'date_joined_program': '2011-07-01',
                     'mentor': 6}
        self.user_url = reverse('profiles_view_profile',
                                kwargs={'display_name': 'Koki'})
        self.user_edit_url = reverse('profiles_edit',
                                     kwargs={'display_name': 'Koki'})
        self.user_delete_url = reverse('profiles_delete',
                                       kwargs={'display_name': 'Koki'})

    def test_view_my_profile_page(self):
        """Get my profile page."""
        c = Client()
        c.login(username='mentor', password='passwd')
        response = c.get(reverse('profiles_view_my_profile'))
        self.assertTemplateUsed(response, 'profiles_view.html')

    def test_view_invite_page(self):
        """Get invite page."""
        c = Client()
        c.login(username='mentor', password='passwd')
        response = c.get(reverse('profiles_invite'))
        self.assertTemplateUsed(response, 'profiles_invite.html')

    def test_view_list_profiles_page(self):
        """Get list profiles page."""
        c = Client()
        response = c.get(reverse('profiles_list_profiles'))
        self.assertTemplateUsed(response, 'profiles_people.html')

    def test_view_profile_page(self):
        """Get profile page."""
        c = Client()
        response = c.get(reverse('profiles_view_profile',
                                 kwargs={'display_name': 'koki'}))
        self.assertTemplateUsed(response, 'profiles_view.html')

    def test_view_edit_profile_page(self):
        """Get edit profile page."""
        c = Client()
        c.login(username='rep', password='passwd')
        response = c.get(reverse('profiles_edit',
                                 kwargs={'display_name': 'koki'}))
        self.assertTemplateUsed(response, 'profiles_edit.html')

    def test_view_delete_profile_page(self):
        """Get delete profile page."""
        c = Client()
        c.login(username='admin', password='passwd')
        response = c.get(reverse('profiles_delete',
                                 kwargs={'display_name': 'koki'}), follow=True)
        self.assertTemplateUsed(response, 'main.html')

    def test_invite_user(self):
        """Test that user is invited."""
        c = Client()
        c.login(username='mentor', password='passwd')
        c.post(reverse('profiles_invite'), {'email': 'foobar@example.com'})

        u = User.objects.get(email='foobar@example.com')
        eq_(u.userprofile.added_by, User.objects.get(username='mentor'))

    def test_edit_profile_permissions(self):
        """Test user permissions to edit profiles."""
        # user edits own profile
        c = Client()
        c.login(username='rep', password='passwd')
        response = c.get(self.user_edit_url, follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

        # admin edits user's profile
        c = Client()
        c.login(username='admin', password='passwd')
        response = c.get(self.user_edit_url, follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

        # third user denied permission to edit user's profile
        c = Client()
        c.login(username='mentor', password='passwd')
        response = c.get(self.user_edit_url, follow=True)
        self.assertTemplateUsed(response, 'main.html')

    def test_edit_profile_redirect(self):
        """Test that after profile redirection is correct.

        When a user edit his own profile must be redirected to
        reverse('profiles_view_my_profile') whereas when editing
        another user's profile, then user must be redirected to
        profile view of the just edited profile.

        """
        c = Client()
        c.login(username='admin', password='passwd')
        response = c.post(self.user_edit_url, self.data, follow=True)
        eq_(response.request['PATH_INFO'], self.user_url)

        c = Client()
        c.login(username='rep', password='passwd')
        response = c.post(self.user_edit_url, self.data, follow=True)
        eq_(response.request['PATH_INFO'], reverse('profiles_view_my_profile'))

    def test_edit_profile(self):
        """Test correct edit of user profile."""
        c = Client()
        c.login(username='rep', password='passwd')

        # edit with correct data
        response = c.post(self.user_edit_url, self.data, follow=True)
        eq_(response.request['PATH_INFO'], reverse('profiles_view_my_profile'))

        # ensure that all user data was saved
        user = User.objects.get(username='rep')
        eq_(user.email, self.data['email'])
        eq_(user.first_name, self.data['first_name'])
        eq_(user.last_name, self.data['last_name'])

        temp_data = self.data.copy()

        eq_(user.userprofile.mentor.id, temp_data['mentor'])
        eq_(user.userprofile.birth_date,
            datetime.date(*(time.strptime(temp_data['birth_date'],
                                          '%Y-%m-%d')[0:3])))

        # delete already checked items
        for item in ['email', 'first_name', 'last_name',
                     'birth_date', 'mentor', 'date_joined_program']:
            del(temp_data[item])

        # ensure that all user profile data was saved
        for field in temp_data.keys():
            eq_(getattr(user.userprofile, field), temp_data[field])

        # test with missing mandatory fields
        mandatory_fields = ['first_name', 'last_name', 'email',
                            'private_email', 'city', 'region',
                            'country', 'lon', 'lat', 'mozillians_profile_url',
                            'irc_name', 'wiki_profile_url']
        for field in mandatory_fields:
            # remove a mandatory field and ensure that edit fails
            temp_data = self.data.copy()
            del(temp_data[field])
            response = c.post(self.user_edit_url, temp_data, follow=True)
            self.assertTemplateUsed(response, 'profiles_edit.html')

    def test_delete_profile(self):
        """Test profile deletion."""
        # user can't delete own profile
        c = Client()
        c.login(username='rep', password='passwd')
        response = c.post(self.user_delete_url, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # admin can delete user's profile
        c = Client()
        c.login(username='admin', password='passwd')
        response = c.post(self.user_delete_url, {'delete': 'true'},
                          follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')

        # third user can't delete user's profile
        c = Client()
        c.login(username='mentor', password='passwd')
        response = c.post(self.user_delete_url, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

    def test_profiles_me(self):
        """Test that user gets own profile rendered."""
        # user gets own profile page rendered
        c = Client()
        c.login(username='rep', password='passwd')
        response = c.get(reverse('profiles_view_my_profile'), follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html')

        # anonymous user get message to login first
        c = Client()
        response = c.get(reverse('profiles_view_my_profile'), follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')

    def test_incomplete_profile(self):
        """Test that user with incomplete profile gets redirected to edit
        page.

        """
        c = Client()
        c.login(username='rep2', password='passwd')
        response = c.get(reverse('profiles_view_my_profile'), follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

    def test_case_insensitive_profile_url(self):
        """Test the display_name is case insensitive in profile urls."""
        c = Client()
        c.login(username='rep', password='passwd')

        response = c.get(reverse('profiles_view_profile',
                                 kwargs={'display_name': 'koki'}), follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html')

        response = c.get(reverse('profiles_view_profile',
                                 kwargs={'display_name': 'Koki'}), follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html')

        response = c.get(reverse('profiles_edit',
                                 kwargs={'display_name': 'koki'}), follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

        response = c.get(reverse('profiles_edit',
                                 kwargs={'display_name': 'Koki'}), follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

    def test_number_of_reps_visibility(self):
        """Test visibility of number of reps based on authentication status."""
        c = Client()

        # try anonymous
        response = c.get(reverse('profiles_list_profiles'), follow=True)
        d = pq(response.content)
        eq_(len(d('#profiles-number-of-reps')), 0)

        # try logged in
        c.login(username='rep', password='passwd')
        response = c.get(reverse('profiles_list_profiles'), follow=True)
        d = pq(response.content)
        eq_(len(d('#profiles-number-of-reps')), 1)

    def test_view_incomplete_profile_page(self):
        """Test permission to view incomplete profile pages.

        Only users with profiles.can_edit_profiles permission can view
        profiles of users with incomplete profiles.

        """
        c = Client()

        # Test as anonymous.
        url = reverse('profiles_view_profile',
                      kwargs={'display_name': 'rep2'})

        response = c.get(url, follow=True)
        self.assertTemplateUsed(response, '404.html',
                                'Anonymous can view the page')

        # Test as logged in w/o permissions.
        c.login(username='rep', password='passwd')
        response = c.get(url, follow=True)
        self.assertTemplateUsed(response, '404.html',
                                'Rep without permission can view the page')

        # Test as admin.
        c.login(username='admin', password='passwd')
        response = c.get(url, follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html',
                                'Admin can\'t view the page')


