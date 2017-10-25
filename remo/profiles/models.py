import datetime
import pytz
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from django_statsd.clients import statsd
from uuslug import uuslug as slugify

from remo.base.utils import get_object_or_none
from remo.base.models import GenericActiveManager
from remo.base.tasks import send_remo_mail
from remo.base.utils import get_date
from remo.celery import app as celery_app
from remo.dashboard.models import ActionItem, Item
from remo.remozilla.models import Bug, WAITING_MENTOR_VALIDATION_ACTION


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


@python_2_unicode_compatible
class MobilisingSkill(models.Model):
    """Mobilising skills."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(blank=True, max_length=100)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    def save(self, *args, **kwargs):
        # Create unique slug
        if not self.slug:
            self.slug = slugify(self.name, instance=self)
        super(MobilisingSkill, self).save(*args, **kwargs)

    def get_absolute_edit_url(self):
        return reverse('edit_mobilising_skills', kwargs={'pk': self.id})

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'mobilising skill'
        verbose_name_plural = 'mobilising skills'


@python_2_unicode_compatible
class MobilisingInterest(models.Model):
    """Mobilising interests."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(blank=True, max_length=100)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    def save(self, *args, **kwargs):
        # Create unique slug
        if not self.slug:
            self.slug = slugify(self.name, instance=self)
        super(MobilisingInterest, self).save(*args, **kwargs)

    def get_absolute_edit_url(self):
        return reverse('edit_mobilising_interests', kwargs={'pk': self.id})

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'mobilising interest'
        verbose_name_plural = 'mobilising interests'


class UserProfile(models.Model):
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
    mobilising_skills = models.ManyToManyField(
        MobilisingSkill, related_name='users_matching_skills')
    mobilising_interests = models.ManyToManyField(
        MobilisingInterest, related_name='users_matching_interests')
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
class UserAvatar(models.Model):
    """User Avatar Model."""
    user = models.OneToOneField(User)
    avatar_url = models.URLField(max_length=400, default='')
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return u'UserAvatar:%s' % self.user.userprofile.display_name


@python_2_unicode_compatible
class UserStatus(models.Model):
    """Model for inactiviy/unavailability data."""
    user = models.ForeignKey(User, related_name='status')
    start_date = models.DateField(blank=True, default=get_date)
    expected_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    replacement_rep = models.ForeignKey(User, null=True, blank=True,
                                        related_name='replaced_rep')
    created_on = models.DateTimeField(auto_now_add=True)
    is_unavailable = models.BooleanField(default=False)

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


@receiver(post_save, sender=UserStatus, dispatch_uid='profiles_user_status_email_reminder')
def user_status_email_reminder(sender, instance, created, raw, **kwargs):
    """Send email notifications when a user submits
    an unavailability notice.
    """

    rep_profile = instance.user.userprofile
    # Make sure that the user has a mentor
    mentor_profile = None
    if instance.user.userprofile.mentor:
        mentor_profile = instance.user.userprofile.mentor.userprofile

    if created:
        subject_rep = 'Confirm if you are available for Reps activities'
        rep_template = 'emails/rep_availability_reminder.jinja'
        notification_datetime = datetime.datetime.combine(
            instance.expected_date - datetime.timedelta(days=1),
            datetime.datetime.min.time())
        data = {'user_status': instance}

        time_diff = (timezone.make_aware(notification_datetime, pytz.UTC) -
                     timezone.now())
        # If the notification date is in the past, then send the notification
        # x/2 hours from now, where x is the diff between the return date and
        # now
        if time_diff.days < 0:
            hours_added = (time_diff.seconds / 3600) / 2
            notification_datetime = (timezone.now() +
                                     datetime.timedelta(hours=hours_added))

        rep_reminder = send_remo_mail.apply_async(
            eta=notification_datetime,
            kwargs={'recipients_list': [rep_profile.user.id],
                    'email_template': rep_template,
                    'subject': subject_rep,
                    'data': data})
        if mentor_profile:
            mentor_template = 'emails/mentor_availability_reminder.jinja'
            subject_mentor = ('Reach out to {0} - '
                              'expected to be available again'
                              .format(instance.user.get_full_name()))
            mentor_reminder = send_remo_mail.apply_async(
                eta=notification_datetime,
                kwargs={'recipients_list': [mentor_profile.user.id],
                        'email_template': mentor_template,
                        'subject': subject_mentor,
                        'data': data})
            (UserProfile.objects.filter(pk=mentor_profile.id)
             .update(unavailability_task_id=mentor_reminder.task_id))

        # Update user profiles with the task IDs
        (UserProfile.objects.filter(pk=rep_profile.id)
         .update(unavailability_task_id=rep_reminder.task_id))
    elif not settings.CELERY_TASK_ALWAYS_EAGER:
        # revoke the tasks in case a user returns sooner
        if rep_profile.unavailability_task_id:
            celery_app.control.revoke(rep_profile.unavailability_task_id)
        if mentor_profile.unavailability_task_id:
            celery_app.control.revoke(mentor_profile.unavailability_task_id)


@receiver(pre_save, sender=UserProfile,
          dispatch_uid='userprofile_set_date_joined_program_pre_save_signal')
def userprofile_set_date_joined_program_pre_save(sender, instance, **kwargs):
    """Set date_joined_program to today when empty."""
    if not instance.date_joined_program:
        instance.date_joined_program = timezone.now().date()


@receiver(pre_save, sender=UserProfile,
          dispatch_uid='userprofile_set_display_name_pre_save_signal')
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


@receiver(pre_save, sender=UserProfile, dispatch_uid='userprofile_email_mentor_notification')
def email_mentor_notification(sender, instance, raw, **kwargs):
    """Notify mentor when his/her mentee changes mentor on his/her profile."""
    if not instance.mentor:
        return

    user_profile = get_object_or_none(UserProfile, user=instance.user)

    if not user_profile or not user_profile.mentor or raw:
        return

    if user_profile.mentor != instance.mentor:
        subject = '[Reps] Mentor reassignment.'
        email_template = 'emails/mentor_change_notification.jinja'
        mentors_recipients = [user_profile.mentor.id, instance.mentor.id]
        rep_recipient = [instance.user.id]
        ctx_data = {'rep_user': instance.user,
                    'new_mentor': instance.mentor}
        send_remo_mail.delay(recipients_list=mentors_recipients,
                             subject=subject,
                             email_template=email_template,
                             data=ctx_data,
                             sender=instance.user.email)
        send_remo_mail.delay(recipients_list=rep_recipient,
                             subject=subject,
                             email_template=email_template,
                             data=ctx_data,
                             sender=instance.mentor.email)
        statsd.incr('profiles.change_mentor')


@receiver(pre_save, sender=UserProfile,
          dispatch_uid='change_mentor_action_items_signal')
def update_mentor_action_items(sender, instance, raw, **kwargs):
    """Update action items when a mentor change occurs."""
    user_profile = get_object_or_none(UserProfile, user=instance.user)
    if user_profile and not raw:
        if user_profile.mentor and user_profile.mentor != instance.mentor:
            action_name = WAITING_MENTOR_VALIDATION_ACTION
            action_model = ContentType.objects.get_for_model(Bug)
            action_items = ActionItem.objects.filter(content_type=action_model,
                                                     name=action_name,
                                                     user=user_profile.mentor)
            action_items.update(user=instance.mentor)


@receiver(post_save, sender=User, dispatch_uid='create_profile_signal')
def create_profile(sender, instance, created, raw, **kwargs):
    """Create a matching profile whenever a user object is created.

    Note that the use of /raw/ prevents conflicts when using loaddata.

    """
    if created and not raw:
        profile, new = UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User, dispatch_uid='user_set_inactive_post_save_signal')
def user_set_inactive_post_save(sender, instance, raw, **kwargs):
    """Set user inactive if there is no associated UserProfile."""
    if raw:
        return

    if (instance.first_name and instance.userprofile and not
            instance.userprofile.registration_complete):
        instance.userprofile.registration_complete = True
        instance.userprofile.save()
