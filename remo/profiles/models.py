import datetime
import re

import django.utils.timezone as timezone

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from south.signals import post_migrate

from remo.base.utils import add_permissions_to_groups

DISPLAY_NAME_MAX_LENGTH = 50

# Monkey patch unicode(User)

def user_unicode(self):
    """Return user's full name and display name if available."""
    if self.userprofile:
        return u'%s :%s' % (self.get_full_name(),
                            self.userprofile.display_name)
    return self.get_full_name()

User.__unicode__ = user_unicode


def _validate_birth_date(data, **kwargs):
    """Validator to ensure age of at least 12 years old."""
    today = datetime.date.today()
    youth_threshold_day = (datetime.date(today.year - 12, today.month,
                                         today.day) +
                           datetime.timedelta(hours=24))

    if data > youth_threshold_day:
        raise ValidationError('Provided Birthdate is not valid.')

    return data


def _validate_mentor(data, **kwargs):
    """Validator to ensure that selected user belongs in the Mentor
    group.

    """
    user = User.objects.get(pk=data)
    if not user.groups.filter(name='Mentor').exists():
        raise ValidationError('Please select a user from the mentor group.')

    return data


class FunctionalArea(models.Model):
    """Mozilla functional areas."""
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class UserProfile(models.Model):
    """Definition of UserProfile Model."""
    user = models.OneToOneField(User)
    registration_complete = models.BooleanField(default=False)
    date_joined_program = models.DateField(blank=True)
    local_name = models.CharField(max_length=100, blank=True, default='')
    birth_date = models.DateField(validators=[_validate_birth_date],
                                  blank=True, null=True)
    city = models.CharField(max_length=50, blank=False, default='')
    region = models.CharField(max_length=50, blank=False, default='')
    country = models.CharField(max_length=50, blank=False, default='')
    lon = models.FloatField(blank=False, null=True)
    lat = models.FloatField(blank=False, null=True)
    display_name = models.CharField(
        max_length=DISPLAY_NAME_MAX_LENGTH, blank=True, default='',
        unique=True,
        validators=[
            RegexValidator(regex=r'("")|(^[A-Za-z0-9_]+$)',
                           message='Please only A-Z characters, numbers and '
                                   'underscores.')])
    private_email = models.EmailField(blank=False, null=True, default='')
    mozillians_profile_url = models.URLField(
        validators=[
            RegexValidator(regex=r'^http(s)?://(www\.)?mozillians.org/',
                           message='Please provide a valid Mozillians url.')])
    twitter_account = models.CharField(
        max_length=16, default='', blank=True,
        validators=[
            RegexValidator(regex=r'("^$")|(^[A-Za-z0-9_]+$)',
                           message='Please provide a valid Twitter handle.')])
    jabber_id = models.CharField(max_length=50, blank=True, default='')
    irc_name = models.CharField(max_length=50, blank=False, default='')
    irc_channels = models.TextField(blank=True, default='')
    linkedin_url = models.URLField(
        blank=True, null=False, default='',
        validators=[
            RegexValidator(regex=r'("^$")|(^http(s)?://(.*?)linkedin.com/)',
                           message='Please provide a valid LinkedIn url.')])
    facebook_url = models.URLField(
        blank=True, null=False, default='',
        validators=[
            RegexValidator(regex=r'("^$")|(^http(s)?://(.*?)facebook.com/)',
                           message='Please provide a valid Facebook url.')])
    diaspora_url = models.URLField(blank=True, null=False, default='')
    personal_website_url = models.URLField(blank=True, null=False, default='')
    personal_blog_feed = models.URLField(blank=True, null=False, default='')
    wiki_profile_url = models.URLField(
        blank=False, null=False, default='',
        validators=[
            RegexValidator(regex=r'^http(s)?://wiki.mozilla.org/User:',
                           message='Please provide a valid wiki url.')])
    added_by = models.ForeignKey(User, null=True, blank=True,
                                 related_name='users_added')
    bio = models.TextField(blank=True, default='')
    gender = models.NullBooleanField(choices=((None, 'Gender'),
                                              (True, 'Female'),
                                              (False, 'Male')),
                                     default=None)
    mentor = models.ForeignKey(User, null=True, blank=False,
                               related_name='mentees',
                               validators=[_validate_mentor])
    functional_areas = models.ManyToManyField(FunctionalArea)
    receive_email_on_add_report = models.BooleanField(null=False,
                                                      blank=True,
                                                      default=True)
    receive_email_on_edit_report = models.BooleanField(null=False,
                                                       blank=True,
                                                       default=False)

    class Meta:
        permissions = (('create_user', 'Can create new user'),
                       ('can_edit_profiles', 'Can edit profiles'),
                       ('can_delete_profiles', 'Can delete profiles'))

    def clean(self, *args, **kwargs):
        """Ensure that added_by variable does not have the same value as
        user variable.

        """
        if self.added_by == self.user:
            raise ValidationError('Field added_by cannot be the same as user.')

        return super(UserProfile, self).clean(*args, **kwargs)

    @property
    def get_age(self):
        """Return the age of the user as an integer.

        Age gets calculated from birth_date variable.
        Snippet from http://djangosnippets.org/snippets/557/

        """
        d = datetime.date.today()
        age = ((d.year - self.birth_date.year) -
               int((d.month, d.day) <
                   (self.birth_date.month, self.birth_date.day)))
        return age


class UserAvatar(models.Model):
    """User Avatar Model."""
    user = models.OneToOneField(User)
    avatar_url = models.URLField(max_length=400, default='')
    last_update = models.DateTimeField(default=(timezone.now() -
                                                datetime.timedelta(hours=25)),
                                       auto_now=True)

    def __unicode__(self):
        return "UserAvatar:%s" % self.user.userprofile.display_name


@receiver(pre_save, sender=UserProfile)
def userprofile_set_date_joined_program_pre_save(sender, instance, **kwargs):
    """Set date_joined_program to today when empty."""
    if not instance.date_joined_program:
        instance.date_joined_program = datetime.date.today()


@receiver(pre_save, sender=UserProfile)
def userprofile_set_display_name_pre_save(sender, instance, **kwargs):
    """Set display_name from user.email if display_name == ''.

    Not setting username because we want to provide human readable,
    nice display names. Username is used only if character limit
    (>DISPLAY_NAME_MAX_LENGTH) is reached.

    Looping to find a unique display_name is not optimal but since we
    are focused on UX we can take some db hits to achieve the best
    possible user experience. Note that we are not expecting more than
    500 registered users on this website, so name conflicts should be
    very limited.

    """
    if not instance.display_name:
        email = instance.user.email.split('@')[0]
        display_name = re.sub(r'[^A-Za-z0-9_]', '_', email)
        display_name = display_name[:DISPLAY_NAME_MAX_LENGTH]

        while True:
            instance.display_name = display_name

            try:
                instance.validate_unique()

            except ValidationError:
                display_name += '_'
                if len(display_name) > DISPLAY_NAME_MAX_LENGTH:
                    # We didn't manage to find a unique display_name
                    # based on email. Just go with calculated username.
                    display_name = instance.user.username

            else:
                break


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, raw, **kwargs):
    """Create a matching profile whenever a user object is created.

    Note that the use of /raw/ prevents conflicts when using loaddata.

    """
    if created and not raw:
        profile, new = UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def user_set_inactive_post_save(sender, instance, raw, **kwargs):
    """Set user inactive if there is no associated UserProfile."""
    if instance.first_name and not raw:
        instance.userprofile.registration_complete = True
        instance.userprofile.save()


@receiver(post_save, sender=User)
def auto_add_to_mentor_group(sender, instance, created, raw, **kwargs):
    """Automatically add new users to Rep group."""
    if created and not raw:
        instance.groups.add(Group.objects.get(name='Rep'))


@receiver(post_migrate)
def report_set_groups(app, sender, signal, **kwargs):
    """Set permissions to groups."""
    if (isinstance(app, basestring) and app != 'profiles'):
        return True

    perms = {'create_user': ['Admin', 'Mentor'],
             'can_edit_profiles': ['Admin'],
             'can_delete_profiles': ['Admin']}

    add_permissions_to_groups('profiles', perms)
