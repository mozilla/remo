import datetime

from nose.tools import eq_, raises
from test_utils import TestCase

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from remo.profiles.models import UserProfile, IRCChannel

class UserTest(TestCase):
    fixtures = ['demo_users.json']

    def setUp(self):
        self.new_user = User.objects.create_user(username="new_user",
                                                 email="new-123@example.com")


    def test_first_name_activates_user(self):
        user = User.objects.get(username="rep2")
        user.first_name = u"Foobar"
        user.save()
        eq_(user.is_active, True)


    def test_new_user_is_inactive(self):
        eq_(self.new_user.is_active, False)


    def test_new_user_gets_profile(self):
        eq_(isinstance(self.new_user.userprofile, UserProfile), True)


    def test_new_user_has_display_name(self):
        eq_(self.new_user.userprofile.display_name, "new_123")


    def tearDown(self):
        self.new_user.delete()


class UserProfileTest(TestCase):
    fixtures = ['demo_users.json']

    def setUp(self):
        self.user = User.objects.get(username="rep")
        self.user_profile = self.user.get_profile()


    def test_bogus_facebook_urls(self):
        facebook_urls = ["http://www.notvalid.com/foo",
                         "https://www.notvalid.com/foo"
                         ]

        @raises(ValidationError)
        def test():
            for facebook_url in facebook_urls:
                self.user_profile.facebook_url = facebook_url
                self.user_profile.full_clean()


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

        @raises(ValidationError)
        def test():
            for linkedin_url in linkedin_urls:
                self.user_profile.linkedin_url = linkedin_url
                self.user_profile.full_clean()


    def test_valid_linkedin_urls(self):
        linkedin_urls = ["http://www.linkedin.com/valid",
                         "http://linkedin.com/valid",
                         "https://linkedin.com/valid",
                         "https://www.linkedin.com/valid",
                         ]

        for linkedin_url in linkedin_urls:
            self.user_profile.linkedin_url = linkedin_url
            self.assertIsNone(self.user_profile.full_clean())


    def test_bogus_mozillians_urls(self):
        mozillians_urls = ["http://www.notvalid.org/foo",
                         "https://www.notvalid.org/foo"
                         ]

        @raises(ValidationError)
        def test():
            for mozillians_url in mozillians_urls:
                self.user_profile.mozillians_url = mozillians_url
                self.user_profile.full_clean()


    def test_valid_mozillians_urls(self):
        mozillians_urls = ["http://www.mozillians.org/valid",
                         "http://mozillians.org/valid",
                         "https://mozillians.org/valid",
                         "https://www.mozillians.org/valid",
                         ]

        for mozillians_url in mozillians_urls:
            self.user_profile.mozillians_url = mozillians_url
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

        @raises(ValidationError)
        def test():
            for date in bogus_dates:
                self.user_profile.birth_date = date
                self.user_profile.full_clean()


    def test_valid_twitter_username(self):
        twitter_usernames = ["@validone", "@valid212", "@va1234567890123",
                             "@_foo_", "@____"]

        @raises(ValidationError)
        def test():
            for twitter_username in twitter_usernames:
                self.user_profile.twitter_username = twitter_username
                self.user_profile.full_clean()


    def test_bogus_twitter_username(self):
        twitter_usernames = ["@bogus*", "@bogus!", "@bogus ",
                             "@1234567890213456"]

        @raises(ValidationError)
        def test():
            for twitter_username in twitter_usernames:
                self.user_profile.twitter_username = twitter_username
                self.user_profile.full_clean()


    def test_valid_gpg_keyid(self):
        gpg_keyids = ["0x88ff88ff", "0x00000000"]


        for gpg_keyid in gpg_keyids:
            self.user_profile.gpg_keyid = gpg_keyid
            self.assertIsNone(self.user_profile.full_clean())


    def test_bogus_gpg_keyid(self):
        gpg_keyids = ["0x0", "0000ffff", "0x000000001", "0xww0000ww"]

        @raises(ValidationError)
        def _test():
            for gpg_keyid in gpg_keyids:
                self.user_profile.gpg_keyid = gpg_keyid
                self.user_profile.full_clean()


    def test_valid_display_name(self):
        display_names = ["foobar", "foo_bar", "_foobar_", "foobar123"]


        for display_name in display_names:
            self.user_profile.display_name = display_name
            self.assertIsNone(self.user_profile.full_clean())


    def test_bogus_display_name(self):
        display_names = ["01234567890123456", "foobar!", "foobar("]

        @raises(ValidationError)
        def _test():
            for display_name in display_names:
                self.user_profile.display_name = display_name
                self.user_profile.full_clean()


    def test_join_mentor_group(self):
        user_profile = User.objects.get(username="rep").get_profile()
        user_profile.join_group("Mentor")

        mentor_group = Group.objects.get(name="Mentor")
        eq_(mentor_group.user_set.count(), 2)


    def test_leave_mentor_group(self):
        user_profile = User.objects.get(username="mentor").get_profile()
        user_profile.leave_group("Mentor")

        mentor_group = Group.objects.get(name="Mentor")
        eq_(mentor_group.user_set.count(), 0)


    def test_join_council_group(self):
        user_profile = User.objects.get(username="rep").get_profile()
        user_profile.join_group("Council")

        council_group = Group.objects.get(name="Council")
        eq_(council_group.user_set.count(), 2)


    def test_leave_council_group(self):
        user_profile = User.objects.get(username="counselor").get_profile()
        user_profile.leave_group("Council")

        council_group = Group.objects.get(name="Council")
        eq_(council_group.user_set.count(), 0)


    def test_join_admin_group(self):
        user_profile = User.objects.get(username="rep").get_profile()
        user_profile.join_group("Admin")

        admin_group = Group.objects.get(name="Admin")
        eq_(admin_group.user_set.count(), 2)


    def test_leave_admin_group(self):
        user_profile = User.objects.get(username="admin").get_profile()
        user_profile.leave_group("Admin")

        admin_group = Group.objects.get(name="Admin")
        eq_(admin_group.user_set.count(), 0)


    def test_join_rep_group(self):
        user_profile = User.objects.get(username="counselor").get_profile()
        user_profile.join_group("Rep")

        rep_group = Group.objects.get(name="Rep")
        eq_(rep_group.user_set.count(), 3)


    def test_leave_rep_group(self):
        user_profile = User.objects.get(username="rep").get_profile()
        user_profile.leave_group("Rep")

        rep_group = Group.objects.get(name="Rep")
        eq_(rep_group.user_set.count(), 1)


    def test_empty_display_name_autogenerate(self):
        self.user_profile.display_name = None
        self.user_profile.save()
        eq_(self.user_profile.display_name, self.user.username)

        self.user_profile.display_name = ''
        self.user_profile.save()
        eq_(self.user_profile.display_name, self.user.username)


    def test_edited_display_name_persists(self):
        self.user_profile.display_name = u"edited"
        self.user_profile.save()
        eq_(self.user_profile.display_name, u"edited")


    def test_user_joins_irc_channel(self):
        self.user_profile.join_irc_channel("#remo")
        eq_(self.user_profile.irc_channels.count(), 1)


    def test_user_leaves_irc_channel(self):
        user_profile = User.objects.get(username="admin").get_profile()
        user_profile.leave_irc_channel("#remo")
        eq_(user_profile.irc_channels.count(), 0)


    def test_user_joins_multiple_irc_channels(self):
        self.user_profile.join_irc_channel("#remo")
        self.user_profile.join_irc_channel("#remo-webdev")
        eq_(self.user_profile.irc_channels.count(), 2)


    @raises(ValueError)
    def test_user_joins_irc_channel_again(self):
        self.user_profile.join_irc_channel("#remo")
        self.user_profile.join_irc_channel("#remo")


    def test_user_joins_new_irc_channel(self):
        self.user_profile.join_irc_channel("#channel_not_in_db")
        eq_(IRCChannel.objects.count(), 4)
        eq_(self.user_profile.irc_channels.count(), 1)


    def test_added_by_valid(self):
        mentor = User.objects.get(username="mentor")
        self.user_profile.added_by = mentor
        self.user_profile.full_clean()


    @raises(ValidationError)
    def test_added_by_bogus(self):
        self.user_profile.added_by = self.user
        self.user_profile.full_clean()
