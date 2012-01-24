import datetime

from nose.tools import eq_
from test_utils import TestCase

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from remo.profiles.models import UserProfile

# test user can join irc channel
# test user can leave irc channel
# test user cannot have to entries with the same irc channel
# test user gpg keyid
# test user auto set display_name
# test user manual set display_name
# test user make/delete admin
# test user make/delete rep
# test user make/delete mentor
# test user make/delete councelor
# test create user, if inactive
# test create user, create profile, if active

class UserProfileTest(TestCase):
    fixtures = ['demo_users.json']

    def setUp(self):
        self.user = User.objects.get(username="rep")
        self.user_profile = self.user.get_profile()


    def test_bogus_facebook_urls(self):
        facebook_urls = ["http://www.notvalid.com/foo",
                         "https://www.notvalid.com/foo"
                         ]

        for facebook_url in facebook_urls:
            self.user_profile.facebook_url = facebook_url
            self.assertRaises(ValidationError, self.user_profile.full_clean)


    def test_valid_facebook_urls(self):
        facebook_urls = ["http://www.facebook.com/valid",
                         "http://facebook.com/valid",
                         "https://facebook.com/valid",
                         "https://www.facebook.com/valid",
                         ]

        for facebook_url in facebook_urls:
            self.user_profile.facebook_url = facebook_url
            self.assertIsNone(self.user_profile.full_clean())


    def test_bogus_linkedin_urls(self):
        linkedin_urls = ["http://www.notvalid.com/foo",
                         "https://www.notvalid.com/foo"
                         ]

        for linkedin_url in linkedin_urls:
            self.user_profile.linkedin_url = linkedin_url
            self.assertRaises(ValidationError, self.user_profile.full_clean)


    def test_valid_linkedin_urls(self):
        linkedin_urls = ["http://www.linkedin.com/valid",
                         "http://linkedin.com/valid",
                         "https://linkedin.com/valid",
                         "https://www.linkedin.com/valid",
                         ]

        for linkedin_url in linkedin_urls:
            self.user_profile.linkedin_url = linkedin_url
            self.assertIsNone(self.user_profile.full_clean())


    def test_valid_birth_date(self):
        today = datetime.date.today()
        bogus_dates = [
            datetime.date(year=1980, month=12, day=2),
            datetime.date(year=today.year-12, month=today.month,
                          day=today.day) - datetime.timedelta(hours=24),
            datetime.date(year=today.year-90, month=today.month,
                          day=today.day) + datetime.timedelta(hours=24)
            ]

        for date in bogus_dates:
            self.user_profile.birth_date = date
            self.assertIsNone(self.user_profile.full_clean())


    def test_bogus_birth_date(self):
        today = datetime.date.today()
        bogus_dates = [
            datetime.date(year=2010, month=5, day=20),
            datetime.date(year=1920, month=6, day=10),
            datetime.date(year=today.year-12, month=today.month,
                          day=today.day) + datetime.timedelta(hours=24),
            datetime.date(year=today.year-90, month=today.month,
                          day=today.day) - datetime.timedelta(hours=24)
            ]

        for date in bogus_dates:
            self.user_profile.birth_date = date
            self.assertRaises(ValidationError, self.user_profile.full_clean)


    def test_valid_twitter_username(self):
        twitter_usernames = ["@validone", "@valid212", "@va1234567890123",
                             "@_foo_", "@____"]

        for twitter_username in twitter_usernames:
            self.user_profile.twitter_username = twitter_username
            self.assertIsNone(self.user_profile.full_clean())


    def test_valid_twitter_username(self):
        twitter_usernames = ["@validone", "@valid212", "@va1234567890123",
                             "@_foo_", "@____"]

        for twitter_username in twitter_usernames:
            self.user_profile.twitter_username = twitter_username
            self.assertIsNone(self.user_profile.full_clean())


    def test_bogus_twitter_username(self):
        twitter_usernames = ["@bogus*", "@bogus!", "@bogus ",
                             "@1234567890213456"]

        for twitter_username in twitter_usernames:
            self.user_profile.twitter_username = twitter_username
            self.assertRaises(ValidationError, self.user_profile.full_clean())


    def test_valid_gpg_keyid(self):
        gpg_keyids = ["0x88ff88ff", "0x00000000"]


        for gpg_keyid in gpg_keyids:
            self.user_profile.gpg_keyid = gpg_keyid
            self.assertIsNone(self.user_profile.full_clean())


    def test_bogus_gpg_keyid(self):
        gpg_keyids = ["0x0", "0000ffff", "0x000000001", "0xww0000ww"]

        for gpg_keyid in gpg_keyids:
            self.user_profile.gpg_keyid = gpg_keyid
            self.assertRaises(ValidationError, self.user_profile.full_clean())

