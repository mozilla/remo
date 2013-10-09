from datetime import timedelta

from celery.task import control as celery_control
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.timezone import now as now_utc

from south.signals import post_migrate
from uuslug import uuslug

from remo.base.utils import add_permissions_to_groups, datetime2pdt
from remo.remozilla.models import Bug
from remo.voting.tasks import send_voting_mail


VOTING_PERIOD_AUTOMATED_POLLS = 3 # in days


class Poll(models.Model):
    """Poll Model."""
    name = models.CharField(max_length=300)
    slug = models.SlugField(blank=True, max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()
    valid_groups = models.ForeignKey(Group, related_name='valid_polls')
    created_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField(validators=[MaxLengthValidator(1500),
                                               MinLengthValidator(20)])
    created_by = models.ForeignKey(User, related_name='range_polls_created')
    users_voted = models.ManyToManyField(User, related_name='polls_voted',
                                         through='Vote')
    task_start_id = models.CharField(max_length=256, blank=True,
                                     null=True, editable=False, default='')
    task_end_id = models.CharField(max_length=256, blank=True, null=True,
                                   editable=False, default='')
    last_notification = models.DateTimeField(null=True)
    bug = models.ForeignKey(Bug, null=True, blank=True)
    automated_poll = models.BooleanField(default=False)

    @property
    def is_future_voting(self):
        if self.start > now_utc():
            return True
        return False

    @property
    def is_current_voting(self):
        if self.start < now_utc() and self.end > now_utc():
            return True
        return False

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['-created_on']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.slug = uuslug(self.name, instance=self)
        elif not settings.CELERY_ALWAYS_EAGER:
            if self.is_current_voting:
                celery_control.revoke(self.task_end_id)
            elif self.is_future_voting:
                celery_control.revoke(self.task_start_id)
                celery_control.revoke(self.task_end_id)
        super(Poll, self).save()


class Vote(models.Model):
    """Vote model."""
    user = models.ForeignKey(User)
    poll = models.ForeignKey(Poll)
    date_voted = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (self.user, self.poll)


class RangePoll(models.Model):
    """Range Poll Model."""
    name = models.CharField(max_length=500, default='')
    poll = models.ForeignKey(Poll, related_name='range_polls')

    def __unicode__(self):
        return self.name


class RangePollChoice(models.Model):
    """Range Poll Choice Model."""
    votes = models.IntegerField(default=0)
    range_poll = models.ForeignKey(RangePoll, related_name='choices')
    nominee = models.ForeignKey(User, limit_choices_to={'groups__name': 'Rep'})

    class Meta:
        ordering = ['-votes', 'nominee__last_name', 'nominee__first_name']


class RadioPoll(models.Model):
    """Radio Poll Model."""
    question = models.CharField(max_length=500)
    poll = models.ForeignKey(Poll, related_name='radio_polls')

    def __unicode__(self):
        return self.question


class RadioPollChoice(models.Model):
    """Radio Poll Choice Model."""
    answer = models.CharField(max_length=500)
    votes = models.IntegerField(default=0)
    radio_poll = models.ForeignKey(RadioPoll, related_name='answers')

    def __unicode__(self):
        return self.answer

    class Meta:
        ordering = ['-votes']


@receiver(post_save, sender=Poll,
          dispatch_uid='voting_poll_email_reminder_signal')
def poll_email_reminder(sender, instance, raw, **kwargs):
    """Send email reminders when a vote starts/ends."""
    subject_start = '[Voting] Cast your vote for "%s" now!' % instance.name
    subject_end = '[Voting] Results for "%s"' % instance.name

    start_template = 'emails/voting_starting_reminder.txt'
    end_template = 'emails/voting_results_reminder.txt'

    if not instance.task_start_id or instance.is_future_voting:
        start_reminder = send_voting_mail.apply_async(
            eta=instance.start, kwargs={'voting_id': instance.id,
                                        'subject': subject_start,
                                        'email_template': start_template})
        (Poll.objects.filter(pk=instance.pk)
                     .update(task_start_id=start_reminder.task_id))
    end_reminder = send_voting_mail.apply_async(
        eta=instance.end, kwargs={'voting_id': instance.id,
                                  'subject': subject_end,
                                  'email_template': end_template})
    (Poll.objects.filter(pk=instance.pk)
                 .update(task_end_id=end_reminder.task_id))


@receiver(pre_delete, sender=Poll,
          dispatch_uid='voting_poll_delete_reminder_signal')
def poll_delete_reminder(sender, instance, **kwargs):
    """Revoke the task if a voting is deleted."""
    if not settings.CELERY_ALWAYS_EAGER:
        if instance.task_start_id:
            celery_control.revoke(instance.task_start_id)
        if instance.task_end_id:
            celery_control.revoke(instance.task_end_id)


@receiver(post_migrate, sender=Poll, dispatch_uid='voting_set_groups_signal')
def voting_set_groups(app, sender, signal, **kwargs):
    """Set permissions to groups."""
    if (isinstance(app, basestring) and app != 'voting'):
        return True

    permissions = (('voting.add_poll', ['Admin']),
                   ('voting.delete_poll', ['Admin']),
                   ('voting.change_poll', ['Admin']))

    add_permissions_to_groups('voting', permissions)


@receiver(post_save, sender=Bug,
          dispatch_uid='remozilla_create_radio_poll_signal')
def create_radio_poll(sender, instance, **kwargs):
    """Create a radio poll automatically.

    If a bug lands in our database with council_vote_requested, create
    a new Poll and let Council members vote.

    """
    if (instance.council_vote_requested
            and not Poll.objects.filter(bug=instance).exists()):
        date_now = datetime2pdt()
        remobot = User.objects.get(username='remobot')

        poll = (Poll.objects
                .create(name=instance.summary,
                        description=instance.first_comment,
                        valid_groups=Group.objects.get(name='Council'),
                        start=date_now,
                        end=(date_now + timedelta(days=VOTING_PERIOD_AUTOMATED_POLLS)),
                        bug=instance,
                        created_by=remobot,
                        automated_poll=True))

        radio_poll = RadioPoll.objects.create(poll=poll,
                                              question='Budget Approval')

        for answer in ('Approved', 'Denied'):
            RadioPollChoice.objects.create(answer=answer, radio_poll=radio_poll)
