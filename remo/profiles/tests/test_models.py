import datetime

from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError

from nose.tools import eq_, ok_, raises
from test_utils import TestCase

from remo.base.tests import RemoTestCase
from remo.profiles.models import DISPLAY_NAME_MAX_LENGTH, UserProfile
from remo.profiles.tests import UserFactory, UserStatusFactory


class UserTest(TestCase):
    """Tests related to User Model."""

    def setUp(self):
        """Setup tests."""
        self.new_user = User.objects.create_user(
            username='new_user',
            email='x' * (DISPLAY_NAME_MAX_LENGTH - 1) + '@example.com')

    def test_first_name_completes_registration(self):
        """Test that filling first_name automatically changes
        registration_complete variable to True.

        """
        rep = UserFactory.create(groups=['Rep'], first_name='',
                                 userprofile__registration_complete=False)
        rep.first_name = u'Foobar'
        rep.save()
        ok_(rep.userprofile.registration_complete)

    def test_new_user_registration_incomplete(self):
        """Test that new users have registration_complete variable set to
        False.

        """
        ok_(not self.new_user.userprofile.registration_complete)

    def test_new_user_gets_profile(self):
        """Test that new users get a UserProfile on creation."""
        ok_(isinstance(self.new_user.userprofile, UserProfile))

    def test_new_user_has_display_name(self):
        """Test that new users get a display_name automatically generated."""
        eq_(self.new_user.userprofile.display_name,
            'x' * (DISPLAY_NAME_MAX_LENGTH - 1))

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
            email='x' * (DISPLAY_NAME_MAX_LENGTH - 1) + '@bar.example.com')

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

    def setUp(self):
        self.mentor = UserFactory.create(groups=['Rep', 'Mentor'])
        self.rep = UserFactory.create(groups=['Rep'],
                                      userprofile__mentor=self.mentor)

    def test_bogus_facebook_urls(self):
        """Test that we reject bogus facebook urls."""
        facebook_urls = ['http://www.notvalid.com/foo',
                         'https://www.notvalid.com/foo', '']

        @raises(ValidationError)
        def test():
            for facebook_url in facebook_urls:
                self.rep.userprofile.facebook_url = facebook_url
                self.rep.userprofile.full_clean()

    def test_valid_facebook_urls(self):
        """Test that we accept only valid facebook urls."""
        facebook_urls = ['http://www.facebook.com/',
                         'http://facebook.com/', 'http://img.facebook.com/',
                         'https://facebook.com/', 'https://www.facebook.com/']

        for facebook_url in facebook_urls:
            self.rep.userprofile.facebook_url = facebook_url
            self.assertIsNone(self.rep.userprofile.full_clean())

    def test_bogus_linkedin_urls(self):
        """Test that we reject bogus linkedin urls."""
        linkedin_urls = ['http://www.notvalid.com/foo',
                         'https://www.notvalid.com/foo']

        @raises(ValidationError)
        def test():
            for linkedin_url in linkedin_urls:
                self.rep.userprofile.linkedin_url = linkedin_url
                self.rep.userprofile.full_clean()

    def test_valid_linkedin_urls(self):
        """Test that we accept only valid linkedin urls."""
        linkedin_urls = ['http://www.linkedin.com/', 'http://linkedin.com/',
                         'http://gr.linkedin.com/',
                         'https://www.linkedin.com/', '']

        for linkedin_url in linkedin_urls:
            self.rep.userprofile.linkedin_url = linkedin_url
            self.assertIsNone(self.rep.userprofile.full_clean())

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
            self.rep.userprofile.mozillians_url = mozillians_url
            self.assertIsNone(self.rep.userprofile.full_clean())

    def test_valid_birth_date(self):
        """Test that we accept birth dates between 12."""
        today = datetime.date.today()
        bogus_dates = [
            datetime.date(year=1980, month=12, day=2),
            datetime.date(year=today.year - 12, month=today.month,
                          day=today.day) - datetime.timedelta(hours=24)]
        for date in bogus_dates:
            self.rep.userprofile.birth_date = date
            self.assertIsNone(self.rep.userprofile.full_clean())

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
                self.rep.userprofile.birth_date = date
                self.rep.userprofile.full_clean()

    def test_valid_twitter_account(self):
        """Test that we accept only valid twitter accounts."""
        twitter_usernames = ['validone', 'valid212', 'va1234567890123',
                             '_foo_', '____', '']

        @raises(ValidationError)
        def test():
            for twitter_account in twitter_usernames:
                self.rep.userprofile.twitter_account = twitter_account
                self.user_profile.full_clean()

    def test_bogus_twitter_username(self):
        """Test that we reject bogus twitter usernames."""
        twitter_usernames = ['bogus*', 'bogus!', 'bogus ', '1234567890213456',
                             '@foobar']

        @raises(ValidationError)
        def test():
            for twitter_account in twitter_usernames:
                self.rep.userprofile.twitter_account = twitter_account
                self.rep.userprofile.full_clean()

    def test_valid_display_name(self):
        """Test that we accept display_name's only with letters and
        underscores.

        """
        display_names = ['foobar', 'foo_bar', '_foobar_', 'foobar123', '']

        for display_name in display_names:
            self.rep.userprofile.display_name = display_name
            self.assertIsNone(self.rep.userprofile.full_clean())

    def test_bogus_display_name(self):
        """Test that we reject display_name's with characters other than
        letters and underscores.

        """
        display_names = ['01234567890123456', 'foobar!', 'foobar(', 'foo bar']

        @raises(ValidationError)
        def _test():
            for display_name in display_names:
                self.rep.userprofile.display_name = display_name
                self.rep.userprofile.full_clean()

    def test_empty_display_name_autogenerate(self):
        """Test that display_name gets autogenerated if None or empty
        string.

        """
        self.rep.userprofile.display_name = None
        self.rep.userprofile.save()
        eq_(self.rep.userprofile.display_name, self.rep.username)

        self.rep.userprofile.display_name = ''
        self.rep.userprofile.save()
        eq_(self.rep.userprofile.display_name, self.rep.username)

    def test_edited_display_name_persists(self):
        """Test that we don't overide display_name with autogenerated
        value if display_name is not empty string.

        """
        self.rep.userprofile.display_name = u'edited'
        self.rep.userprofile.save()
        eq_(self.rep.userprofile.display_name, u'edited')

    def test_added_by_valid(self):
        """Test that added_by is a valid user.

        """
        self.rep.userprofile.added_by = self.mentor
        self.rep.userprofile.full_clean()

    @raises(ValidationError)
    def test_added_by_bogus(self):
        """Test that added_by is not the same as user.

        """
        self.rep.userprofile.added_by = self.rep
        self.rep.userprofile.full_clean()

    def test_bogus_mentor(self):
        """Test mentor change. """
        user = UserFactory.create(groups=['Rep'])
        self.rep.userprofile.mentor = user
        self.assertRaises(ValidationError, self.rep.userprofile.full_clean)
        self.rep.userprofile.mentor = self.mentor
        self.rep.userprofile.full_clean()


class PermissionTest(TestCase):
    """Tests related to User Permissions."""

    def setUp(self):
        """Setup tests."""
        self.permissions = [
            'profiles.create_user',
            'profiles.can_edit_profiles']

    def test_admin_group_has_all_permissions(self):
        """Test that admin group has all permissions."""
        admin = UserFactory.create(groups=['Admin'])
        for permission in self.permissions:
            ok_(admin.has_perm(permission))

    def test_council_group_has_no_permissions(self):
        """Test that council group has no permissions."""
        councelor = UserFactory.create(groups=['Council'])
        for permission in self.permissions:
            ok_(not councelor.has_perm(permission))

    def test_mentor_group_has_one_permission(self):
        """Test that mentor group has only create_user permission."""
        mentor = UserFactory.create(groups=['Mentor'])
        for permission in self.permissions:
            if permission == 'profiles.create_user':
                ok_(mentor.has_perm(permission))
            else:
                ok_(not mentor.has_perm(permission))

    def test_rep_group_has_no_permissions(self):
        """Test that rep group has no permissions."""
        user = UserFactory.create(groups=['Rep'])
        for permission in self.permissions:
            ok_(not user.has_perm(permission))


class EmailMentorNotification(RemoTestCase):
    """Test that a mentor receives an email when a Mente changes  mentor."""

    def test_send_email_on_mentor_change(self):
        """Test that old mentor gets an email."""
        new_mentor = UserFactory.create(groups=['Rep', 'Mentor'])
        old_mentor = UserFactory.create(groups=['Rep', 'Mentor'])
        user = UserFactory.create(groups=['Rep'],
                                  userprofile__mentor=old_mentor)
        user.userprofile.mentor = new_mentor
        user.userprofile.save()
        eq_(len(mail.outbox), 3)
        recipients = set([mail.outbox[0].to[0],
                          mail.outbox[1].to[0],
                          mail.outbox[2].to[0]])
        receivers = set(['{0} <{1}>'.format(new_mentor.get_full_name(),
                                            new_mentor.email),
                         '{0} <{1}>'.format(old_mentor.get_full_name(),
                                            old_mentor.email),
                         '{0} <{1}>'.format(user.get_full_name(),
                                            user.email)])
        eq_(recipients, receivers)
        eq_(set([msg.extra_headers['Reply-To'] for msg in mail.outbox]),
            set([new_mentor.email, user.email]))


class UserStatusNotification(RemoTestCase):
    """Tests email notifications when a user becomes unavailable."""

    def test_base(self):
        mentor = UserFactory.create()
        rep = UserFactory.create(userprofile__mentor=mentor)
        UserStatusFactory.create(user=rep)
        eq_(len(mail.outbox), 2)
        eq_(mail.outbox[0].subject,
            'Confirm if you are available for Reps activities')
        msg = ('Reach out to {0} - expected to be available again'
               .format(rep.get_full_name()))
        eq_(mail.outbox[1].subject, msg)
        eq_(mail.outbox[0].to[0],
            '{0} <{1}>'.format(rep.get_full_name(), rep.email))
        eq_(mail.outbox[1].to[0],
            '{0} <{1}>'.format(mentor.get_full_name(), mentor.email))
