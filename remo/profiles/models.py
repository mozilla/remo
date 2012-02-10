import datetime
import re
import urlparse

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from libravatar import libravatar_url


def _validate_birth_date(data, **kwargs):
    today = datetime.date.today()
    youth_threshold_day = datetime.date(today.year-12, today.month, today.day)+\
                          datetime.timedelta(hours=24)

    maturity_threshold_day = datetime.date(today.year-90, today.month, today.day)-\
                             datetime.timedelta(hours=24)

    if data < youth_threshold_day and data > maturity_threshold_day:
        return data

    else:
        raise ValidationError("Provided Birthdate is not valid.")


def _validate_twitter_username(data, **kwargs):
    if data == "" or re.match(r'([A-Za-z0-9_]+)', data):
        return data

    else:
        raise ValidationError("Provided Twitter Username is not valid.")


def _validate_display_name(data, **kwargs):
    if data == "" or re.match(r'[A-Za-z_]+', data):
        return data

    else:
        raise ValidationError("Provided Display Name is not valid.")


def _validate_mentor(data, **kwargs):
    user = User.objects.get(pk=data)

    if user.groups.filter(name="Mentor").count():
        return data

    else:
        raise ValidationError("Selected user does not belong to mentor group")


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    registration_complete = models.BooleanField(default=False)
    local_name = models.CharField(max_length=50, blank=True, default="")
    birth_date = models.DateField(validators=[_validate_birth_date],
                                  null=True)
    city = models.CharField(max_length=30, blank=False, default="")
    region = models.CharField(max_length=30, blank=False, default="")
    country = models.CharField(max_length=30, blank=False, default="")
    lon = models.FloatField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    display_name = models.CharField(max_length=15, blank=True, default="",
                                    unique=True,
                                    validators=[_validate_display_name])
    private_email = models.EmailField(blank=False, null=True, default="")
    mozillians_profile_url = models.URLField(
        verify_exists=True,
        validators=[
            RegexValidator(regex=r'http(s)?://(www.)?mozillians.org/',
                           message="Provided Mozillians url is not valid."),
            ])
    twitter_account = models.CharField(max_length=16, default="",
                                       validators=[_validate_twitter_username],
                                       blank=True)
    jabber_id = models.CharField(max_length=50, blank=True, default="")
    irc_name = models.CharField(max_length=30, blank=False, default="")
    irc_channels = models.TextField(blank=True, default="")
    linkedin_url = models.URLField(
        blank=True, null=True, default="", verify_exists=True,
        validators=[
            RegexValidator(regex=r'('')|(http(s)?://(www.)?linkedin.com/)',
                           message="Provided LinkedIn url is not valid.")
            ])
    facebook_url = models.URLField(
        blank=True, null=True, default="", verify_exists=True,
        validators=[
            RegexValidator(regex=r'('')|(http(s)?://(www.)?facebook.com/)',
                           message="Provided Facebook url is not valid.")
            ])
    diaspora_url = models.URLField(blank=True, null=True, default="",
                                   verify_exists=True)
    personal_website_url = models.URLField(blank=True, null=True, default="",
                                           verify_exists=True)
    personal_blog_feed = models.URLField(blank=True, null=True, default="",
                                         verify_exists=True)
    added_by = models.ForeignKey(User, null=True, blank=True,
                                 related_name="users_added")
    bio = models.TextField(blank=True, default="")
    gender = models.NullBooleanField(choices=((True, "Female"),
                                              (False, "Male")),
                                     default=None)
    mentor = models.ForeignKey(User, null=True, blank=True,
                               related_name="mentors_users",
                               validators=[_validate_mentor])

    class Meta:
        permissions = (
            ("create_user", "Can create new user"),
            ("can_edit_profiles", "Can edit profiles"),
            )

    def clean(self, *args, **kwargs):
        # ensure that added_by is not the same as user <-- Make sure your comments are of the format
        # """This is my comment and it is a sentence."""
        if self.added_by == self.user:
            raise ValidationError("added_by cannot be the same as user")

        return super(UserProfile, self).clean(*args, **kwargs)

    @property
    def get_age(self):
        # snippet from http://djangosnippets.org/snippets/557/
        d = datetime.date.today()
        age = (d.year - self.birth_date.year) -\
              int((d.month, d.day) <\
                  (self.birth_date.month, self.birth_date.day))
        return age

    def get_avatar_url(self, size=128):
        default_img_url = reduce(lambda u, x: urlparse.urljoin(u, x),
                                 [settings.SITE_URL,
                                  settings.MEDIA_URL,
                                  'img/remo/remo_avatar.png'])

        return libravatar_url(email=self.user.email,
                              default=default_img_url,
                              size=size)


@receiver(pre_save, sender=UserProfile)
def userprofile_set_display_name_pre_save(sender, instance, **kwargs):
    # Comments should be of a sentence structure and end in a period.
    """
    Set display_name from user.email if display_name == ''

    Not setting username because we want to provide human readable,
    nice display names. Username is used only if character limit is
    reached
    """
    # I'm not sure if a user's email address is a good indicator of human
    # readable-ness, since someone could have something like bb@mozilla.com
    if not instance.display_name:
        email = instance.user.email.split('@')[0]
        display_name = re.sub(r'[^A-Za-z0-9_]', '_', email)

        while True:
            # This seems like an inefficient way to find a username and
            # should be rewritten in a different way or the username should
            # just be applied as the default behaviour.
            instance.display_name = display_name

            try:
                instance.validate_unique()

            except ValidationError:
                display_name += '_'
                if len(display_name) > 15:
                    # oops! just try username, sorry
                    display_name = instance.user.username

            else:
                break


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, raw, **kwargs):
    """
    Create a matching profile whenever a user object is created.

    Use of /raw/ prevents conflicts when using loaddata
    """
    if created and not raw:
        profile, new = UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def user_set_inactive_post_save(sender, instance, raw, **kwargs):
    """
    Set user inactive if there is no associated UserProfile
    """
    if instance.first_name and not raw:
        instance.userprofile.registration_complete = True
        instance.userprofile.save()


@receiver(post_save, sender=User)
def auto_add_to_mentor_group(sender, instance, created, raw, **kwargs):
    """
    Automatically add new users to Rep group
    """
    if created and not raw:
        instance.groups.add(Group.objects.get(name="Rep"))
