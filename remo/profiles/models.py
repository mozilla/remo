import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

import caching.base
from uuslug import uuslug as slugify

from remo.base.models import GenericActiveManager
from remo.base.utils import get_date
from remo.dashboard.models import ActionItem, Item


DISPLAY_NAME_MAX_LENGTH = 50
NOMINATION_ACTION_ITEM = u'Nominate mentees for the month of'
NOMINATION_END_DAY = 10


def user_unicode(self):
    """Return user's full name."""
    return self.get_full_name()


# Monkey patch unicode(User)
User.__unicode__ = user_unicode


def _validate_birth_date(data, **kwargs):
    """Validator to ensure age of at least 12 years old."""
    today = timezone.now().date()
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


@python_2_unicode_compatible
class FunctionalArea(models.Model):
    """Mozilla functional areas."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(blank=True, max_length=100)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    def save(self, *args, **kwargs):
        # Create unique slug
        if not self.slug:
            self.slug = slugify(self.name, instance=self)
        super(FunctionalArea, self).save(*args, **kwargs)

    def get_absolute_edit_url(self):
        return reverse('edit_functional_area', kwargs={'pk': self.id})

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'functional area'
        verbose_name_plural = 'functional areas'


class UserProfile(caching.base.CachingMixin, models.Model):
    """Definition of UserProfile Model."""
    user = models.OneToOneField(User)
    registration_complete = models.BooleanField(default=False)
    date_joined_program = models.DateField(blank=True)
    date_left_program = models.DateField(blank=True, null=True)
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
        blank=True, null=False, default='',
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
    mentor = models.ForeignKey(User, null=True, blank=True,
                               related_name='mentees',
                               validators=[_validate_mentor],
                               on_delete=models.SET_NULL)
    functional_areas = models.ManyToManyField(
        FunctionalArea, related_name='users_matching')
    tracked_functional_areas = models.ManyToManyField(
        FunctionalArea, related_name='users_tracking')
    receive_email_on_add_comment = models.BooleanField(null=False,
                                                       blank=True,
                                                       default=True)
    receive_email_on_add_event_comment = models.BooleanField(null=False,
                                                             blank=True,
                                                             default=True)
    receive_email_on_add_voting_comment = models.BooleanField(null=False,
                                                              blank=True,
                                                              default=True)
    mozillian_username = models.CharField(blank=True, default='',
                                          max_length=40)
    current_streak_start = models.DateField(null=True, blank=True)
    longest_streak_start = models.DateField(null=True, blank=True)
    longest_streak_end = models.DateField(null=True, blank=True)
    first_report_notification = models.DateField(null=True, blank=True)
    second_report_notification = models.DateField(null=True, blank=True)
    timezone = models.CharField(max_length=100, blank=True, default='')
    unavailability_task_id = models.CharField(max_length=256, blank=True,
                                              null=True, editable=False,
                                              default='')
    is_rotm_nominee = models.BooleanField(default=False)
    rotm_nominated_by = models.ForeignKey(User, null=True, blank=True,
                                          related_name='rotm_nominations',
                                          validators=[_validate_mentor],
                                          on_delete=models.SET_NULL)
    action_items = generic.GenericRelation('dashboard.ActionItem')

    objects = caching.base.CachingManager()

    class Meta:
        permissions = (('create_user', 'Can create new user'),
                       ('can_edit_profiles', 'Can edit profiles'),
                       ('can_delete_profiles', 'Can delete profiles'))

    def get_absolute_url(self):
        return reverse('remo.profiles.views.view_profile',
                       kwargs={'display_name': self.display_name})

    @property
    def get_age(self):
        """Return the age of the user as an integer.

        Age gets calculated from birth_date variable.
        Snippet from http://djangosnippets.org/snippets/557/

        """
        d = timezone.now().date()
        age = ((d.year - self.birth_date.year) -
               int((d.month, d.day) <
                   (self.birth_date.month, self.birth_date.day)))
        return age

    def clean(self, *args, **kwargs):
        """Ensure that added_by variable does not have the same value as
        user variable.

        """
        if self.added_by == self.user:
            raise ValidationError('Field added_by cannot be the same as user.')

        return super(UserProfile, self).clean(*args, **kwargs)

    def get_action_items(self):
        """Return a list of Action Items relevant to this model."""

        today = timezone.now().date()
        due_date = datetime.date(today.year, today.month, NOMINATION_END_DAY)
        name = u'{0} {1}'.format(NOMINATION_ACTION_ITEM, today.strftime('%B'))
        priority = ActionItem.NORMAL
        action_item = Item(name, self.user, priority, due_date)

        return [action_item]


@python_2_unicode_compatible
class UserAvatar(caching.base.CachingMixin, models.Model):
    """User Avatar Model."""
    user = models.OneToOneField(User)
    avatar_url = models.URLField(max_length=400, default='')
    last_update = models.DateTimeField(auto_now=True)

    objects = caching.base.CachingManager()

    def __str__(self):
        return u'UserAvatar:%s' % self.user.userprofile.display_name


@python_2_unicode_compatible
class UserStatus(caching.base.CachingMixin, models.Model):
    """Model for inactiviy/unavailability data."""
    user = models.ForeignKey(User, related_name='status')
    start_date = models.DateField(blank=True, default=get_date)
    expected_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    replacement_rep = models.ForeignKey(User, null=True, blank=True,
                                        related_name='replaced_rep')
    created_on = models.DateTimeField(auto_now_add=True)
    is_unavailable = models.BooleanField(default=False)

    objects = caching.base.CachingManager()

    @property
    def is_future_date(self):
        if self.expected_date > timezone.now().date():
            return True
        return False

    def __str__(self):
        return self.user.get_full_name()

    def save(self, *args, **kwargs):
        # Save the timestamp when a Rep becomes available
        if not self.id and self.start_date <= get_date():
            self.is_unavailable = True
        if self.id and self.is_unavailable:
            self.is_unavailable = False
            self.return_date = timezone.now().date()
        super(UserStatus, self).save()

    class Meta:
        verbose_name_plural = 'User Statuses'
        ordering = ['-expected_date', '-created_on']
