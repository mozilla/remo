import datetime
import pytz
import re

from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.utils import timezone

from remo.base.utils import get_object_or_none
from remo.base.tasks import send_remo_mail
from remo.celery import app as celery_app
from remo.dashboard.models import ActionItem
from remo.profiles.models import UserProfile, UserStatus
from remo.remozilla.models import Bug, WAITING_MENTOR_VALIDATION_ACTION


DISPLAY_NAME_MAX_LENGTH = 50
NOMINATION_ACTION_ITEM = u'Nominate mentees for the month of'
NOMINATION_END_DAY = 10


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
