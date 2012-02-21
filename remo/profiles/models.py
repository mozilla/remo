import datetime
import re
import urlparse

from django.db import models
from django.db.models.signals import post_save, pre_save
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.dispatch import receiver

from libravatar import libravatar_url


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


class UserProfile(models.Model):
    """Definition of UserProfile Model."""
    user = models.OneToOneField(User)
    registration_complete = models.BooleanField(default=False)
    local_name = models.CharField(max_length=50, blank=True, default='')
    birth_date = models.DateField(validators=[_validate_birth_date],
                                  null=True)
    city = models.CharField(max_length=30, blank=False, default='')
    region = models.CharField(max_length=30, blank=False, default='')
    country = models.CharField(max_length=30, blank=False, default='')
    lon = models.FloatField(blank=False, null=True)
    lat = models.FloatField(blank=False, null=True)
    display_name = models.CharField(
        max_length=15, blank=True, default='', unique=True,
        validators=[
            RegexValidator(regex=r'("")|([A-Za-z0-9_]+)',
                           message='Please only A-Z characters, numbers and '
                                   'underscores.')])
    private_email = models.EmailField(blank=False, null=True, default='')
    mozillians_profile_url = models.URLField(
        verify_exists=True,
        validators=[
            RegexValidator(regex=r'^http(s)?://(www.)?mozillians.org/',
                           message='Please provide a valid Mozillians url.')])
    twitter_account = models.CharField(
        max_length=16, default='', blank=True,
        validators=[
            RegexValidator(regex=r'("^$")|(^[A-Za-z0-9_]+)',
                           message='Please provide a valid Twitter handle.')])
    jabber_id = models.CharField(max_length=50, blank=True, default='')
    irc_name = models.CharField(max_length=30, blank=False, default='')
    irc_channels = models.TextField(blank=True, default='')
    linkedin_url = models.URLField(
        blank=True, null=False, default='', verify_exists=True,
        validators=[
            RegexValidator(regex=r'("^$")|(^http(s)?://(www.)?linkedin.com/)',
                           message='Please provide a valid LinkedIn url.')])
    facebook_url = models.URLField(
        blank=True, null=False, default='', verify_exists=True,
        validators=[
            RegexValidator(regex=r'("^$")|(^http(s)?://(www.)?facebook.com/)',
                           message='Please provide a valid Facebook url.')])
    diaspora_url = models.URLField(blank=True, null=False, default='',
                                   verify_exists=True)
    personal_website_url = models.URLField(blank=True, null=False, default='',
                                           verify_exists=True)
    personal_blog_feed = models.URLField(blank=True, null=False, default='',
                                         verify_exists=True)
    wiki_profile_url = models.URLField(
        blank=False, null=False, default='', verify_exists=True,
        validators=[
            RegexValidator(regex=r'^http(s)?://wiki.mozilla.org/User:',
                           message='Please provide a valid wiki url.')])
    added_by = models.ForeignKey(User, null=True, blank=True,
                                 related_name='users_added')
    bio = models.TextField(blank=True, default='')
    gender = models.NullBooleanField(choices=((True, 'Female'),
                                              (False, 'Male')),
                                     default=None)
    mentor = models.ForeignKey(User, null=True, blank=True,
                               related_name='mentors_users',
                               validators=[_validate_mentor])

    class Meta:
        permissions = (
            ('create_user', 'Can create new user'),
            ('can_edit_profiles', 'Can edit profiles'),
            )

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

    def get_avatar_url(self, size=128):
        """Get a url pointing to user's avatar.

        The libravatar network is used for avatars. Optional argument
        size can be provided to set the avatar size.
        """
        default_img_url = reduce(lambda u, x: urlparse.urljoin(u, x),
                                 [settings.SITE_URL,
                                  settings.MEDIA_URL,
                                  'img/remo/remo_avatar.png'])

        return libravatar_url(email=self.user.email,
                              default=default_img_url,
                              size=size)


@receiver(pre_save, sender=UserProfile)
def userprofile_set_display_name_pre_save(sender, instance, **kwargs):
    """Set display_name from user.email if display_name == ''.

    Not setting username because we want to provide human readable,
    nice display names. Username is used only if character limit (>15)
    is reached.

    Looping to find a unique display_name is not optimal but since we
    are focused on UX we can take some db hits to achieve the best
    possible user experience. Note that we are not expecting more than
    500 registered users on this website, so name conflicts should be
    very limited.
    """
    if not instance.display_name:
        email = instance.user.email.split('@')[0]
        display_name = re.sub(r'[^A-Za-z0-9_]', '_', email)

        while True:
            instance.display_name = display_name

            try:
                instance.validate_unique()

            except ValidationError:
                display_name += '_'
                if len(display_name) > 15:
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
