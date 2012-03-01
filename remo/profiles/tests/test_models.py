import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from nose.tools import eq_, raises
from test_utils import TestCase

from remo.profiles.models import DISPLAY_NAME_MAX_LENGTH, UserProfile


class UserTest(TestCase):
    """Tests related to User Model."""
    fixtures = ['demo_users.json']

    def setUp(self):
        """Setup tests."""
        self.new_user = User.objects.create_user(
            username='new_user',
            email='x' * (DISPLAY_NAME_MAX_LENGTH - 1) + '@example.com')

    def test_first_name_completes_registration(self):
        """Test that filling first_name automatically changes
        registration_complete variable to True.

        """
        user = User.objects.get(username='rep2')
        user.first_name = u'Foobar'
        user.save()
        eq_(user.userprofile.registration_complete, True)

    def test_new_user_registration_incomplete(self):
        """Test that new users have registration_complete variable set to
        False.

        """
        eq_(self.new_user.userprofile.registration_complete, False)

    def test_new_user_gets_profile(self):
        """Test that new users get a UserProfile on creation."""
        eq_(isinstance(self.new_user.userprofile, UserProfile), True)

    def test_new_user_has_display_name(self):
        """Test that new users get a display_name automatically generated."""
        eq_(self.new_user.userprofile.display_name,
            'x' * (DISPLAY_NAME_MAX_LENGTH - 1))

    def test_new_user_joins_rep_group(self):
        """Test that new users join the Rep group automatically."""
        eq_(self.new_user.groups.filter(name='Rep').count(), 1)

    def test_new_user_conflicting_display_names(self):
        """Test that display_name automatic calculation function will
        append _'s to conflicting display names and that will stop and
        use username if no unique display_name is generated with 50
        characters or less.

        """
        # First create a new user for whom we can calculate a
        # display_name with appended _'s.
        new_user2 = User.objects.create_user(
            username='conflicting',
            email= 'x' * (DISPLAY_NAME_MAX_LENGTH - 1) + '@bar.example.com')

        eq_(new_user2.userprofile.display_name,
            'x' * (DISPLAY_NAME_MAX_LENGTH - 1) + '_')

        # Then create a new user for whom we can't calculate a
        # display_name since it exceeds 15 characters. Instead we use
        # username for display_name
        new_user3 = User.objects.create_user(
            username='conflicting2',
            email='x' * (DISPLAY_NAME_MAX_LENGTH - 1) + '@foo.example.com')

        eq_(new_user3.userprofile.display_name, new_user3.username)

    def test_initial_display_name_larger_than_max(self):
        """Test that when a user with email username larger than
        DISPLAY_NAME_MAX_LENGTH gets an auto-generated name stripped
        down to DISPLAY_NAME_MAX_LENGTH.

        """
        new_user = User.objects.create_user(
            username='dummyusername',
            email=('x' * (DISPLAY_NAME_MAX_LENGTH + 10)) + '@example.com')

        eq_(new_user.userprofile.display_name, 'x' * DISPLAY_NAME_MAX_LENGTH)


class UserProfileTest(TestCase):
    """Tests related to UserProfile Model."""
    fixtures = ['demo_users.json']

    def setUp(self):
        """Setup tests."""
        self.user = User.objects.get(username='rep')
        self.user_profile = self.user.get_profile()

    def test_bogus_facebook_urls(self):
        """Test that we reject bogus facebook urls."""
        facebook_urls = ['http://www.notvalid.com/foo',
                         'https://www.notvalid.com/foo', '']

        @raises(ValidationError)
        def test():
            for facebook_url in facebook_urls:
                self.user_profile.facebook_url = facebook_url
                self.user_profile.full_clean()

    def test_valid_facebook_urls(self):
        """Test that we accept only valid facebook urls."""
        facebook_urls = ['http://www.facebook.com/', 'http://facebook.com/',
                         'https://facebook.com/', 'https://www.facebook.com/']

        for facebook_url in facebook_urls:
            self.user_profile.facebook_url = facebook_url
            self.assertIsNone(self.user_profile.full_clean())

    def test_bogus_linkedin_urls(self):
        """Test that we reject bogus linkedin urls."""
        linkedin_urls = ['http://www.notvalid.com/foo',
                         'https://www.notvalid.com/foo']

        @raises(ValidationError)
        def test():
            for linkedin_url in linkedin_urls:
                self.user_profile.linkedin_url = linkedin_url
                self.user_profile.full_clean()

    def test_valid_linkedin_urls(self):
        """Test that we accept only valid linkedin urls."""
        linkedin_urls = ['http://www.linkedin.com/', 'http://linkedin.com/',
                         'https://www.linkedin.com/', '']

        for linkedin_url in linkedin_urls:
            self.user_profile.linkedin_url = linkedin_url
            self.assertIsNone(self.user_profile.full_clean())

    def test_bogus_mozillians_urls(self):
        """Test that we reject bogus mozillians urls."""
        mozillians_urls = ['http://www.notvalid.org/foo',
                           'https://www.notvalid.org/foo', '']

        @raises(ValidationError)
        def test():
            for mozillians_url in mozillians_urls:
                self.user_profile.mozillians_url = mozillians_url
                self.user_profile.full_clean()

    def test_valid_mozillians_urls(self):
        """Test that we accept only valid mozillians urls."""
        mozillians_urls = ['http://www.mozillians.org/valid',
                           'http://mozillians.org/valid',
                           'https://mozillians.org/valid',
                           'https://www.mozillians.org/valid']

        for mozillians_url in mozillians_urls:
            self.user_profile.mozillians_url = mozillians_url
            self.assertIsNone(self.user_profile.full_clean())

    def test_valid_birth_date(self):
        """Test that we accept birth dates between 12 and 90 years old."""
        today = datetime.date.today()
        bogus_dates = [
            datetime.date(year=1980, month=12, day=2),
            datetime.date(year=today.year - 12, month=today.month,
                          day=today.day) - datetime.timedelta(hours=24),
            datetime.date(year=today.year - 90, month=today.month,
                          day=today.day) + datetime.timedelta(hours=24)]

        for date in bogus_dates:
            self.user_profile.birth_date = date
            self.assertIsNone(self.user_profile.full_clean())

    def test_bogus_birth_date(self):
        """Test that we reject birth dates younger 12 or older 90 years old."""
        today = datetime.date.today()
        bogus_dates = [
            datetime.date(year=2010, month=5, day=20),
            datetime.date(year=1920, month=6, day=10),
            datetime.date(year=today.year - 12, month=today.month,
                          day=today.day) + datetime.timedelta(hours=24)]

        @raises(ValidationError)
        def test():
            for date in bogus_dates:
                self.user_profile.birth_date = date
                self.user_profile.full_clean()

    def test_valid_twitter_username(self):
        """Test that we accept only valid twitter usernames."""
        twitter_usernames = ['validone', 'valid212', 'va1234567890123',
                             '_foo_', '____', '']

        @raises(ValidationError)
        def test():
            for twitter_username in twitter_usernames:
                self.user_profile.twitter_username = twitter_username
                self.user_profile.full_clean()

    def test_bogus_twitter_username(self):
        """Test that we reject bogus twitter usernames."""
        twitter_usernames = ['bogus*', 'bogus!', 'bogus ', '1234567890213456',
                             '@foobar']

        @raises(ValidationError)
        def test():
            for twitter_username in twitter_usernames:
                self.user_profile.twitter_username = twitter_username
                self.user_profile.full_clean()

    def test_valid_display_name(self):
        """Test that we accept display_name's only with letters and
        underscores.

        """
        display_names = ['foobar', 'foo_bar', '_foobar_', 'foobar123', '']

        for display_name in display_names:
            self.user_profile.display_name = display_name
            self.assertIsNone(self.user_profile.full_clean())

    def test_bogus_display_name(self):
        """Test that we reject display_name's with characters other than
        letters and underscores.

        """
        display_names = ['01234567890123456', 'foobar!', 'foobar(']

        @raises(ValidationError)
        def _test():
            for display_name in display_names:
                self.user_profile.display_name = display_name
                self.user_profile.full_clean()

    def test_empty_display_name_autogenerate(self):
        """Test that display_name gets autogenerated if None or empty
        string.

        """
        self.user_profile.display_name = None
        self.user_profile.save()
        eq_(self.user_profile.display_name, self.user.username)

        self.user_profile.display_name = ''
        self.user_profile.save()
        eq_(self.user_profile.display_name, self.user.username)

    def test_edited_display_name_persists(self):
        """Test that we don't overide display_name with autogenerated
        value if display_name is not empty string.

        """
        self.user_profile.display_name = u'edited'
        self.user_profile.save()
        eq_(self.user_profile.display_name, u'edited')

    def test_added_by_valid(self):
        """Test that added_by is a valid user.

        """
        mentor = User.objects.get(username='mentor')
        self.user_profile.added_by = mentor
        self.user_profile.full_clean()

    @raises(ValidationError)
    def test_added_by_bogus(self):
        """Test that added_by is not the same as user.

        """
        self.user_profile.added_by = self.user
        self.user_profile.full_clean()

    def test_valid_mentor(self):
        """Test that mentor belongs to the Mentor group.

        """
        mentor = User.objects.filter(groups__name='Mentor')[0]
        self.user_profile.mentor = mentor
        self.user_profile.full_clean()

    @raises(ValidationError)
    def test_bogus_mentor(self):
        """Test that if mentor does not belong to the Mentor group,
        exception is raised.

        """
        mentor = User.objects.exclude(groups__name='Mentor')[0]
        self.user_profile.mentor = mentor
        self.user_profile.full_clean()


class PermissionTest(TestCase):
    """Tests related to User Permissions."""
    fixtures = ['demo_users.json']

    def setUp(self):
        """Setup tests."""
        self.permissions = [
            'profiles.create_user',
            'profiles.can_edit_profiles']

    def test_admin_group_has_all_permissions(self):
        """Test that admin group has all permissions."""
        user = User.objects.get(username='admin')
        for permission in self.permissions:
            eq_(user.has_perm(permission), True)

    def test_council_group_has_no_permissions(self):
        """Test that council group has no permissions."""
        user = User.objects.get(username='counselor')
        for permission in self.permissions:
            eq_(user.has_perm(permission), False)

    def test_mentor_group_has_one_permission(self):
        """Test that mentor group has only create_user permission."""
        user = User.objects.get(username='mentor')
        for permission in self.permissions:
            if permission == 'profiles.create_user':
                eq_(user.has_perm(permission), True)
            else:
                eq_(user.has_perm(permission), False)

    def test_rep_group_has_no_permissions(self):
        """Test that rep group has no permissions."""
        user = User.objects.get(username='rep')
        for permission in self.permissions:
            eq_(user.has_perm(permission), False)
