from celery.task import control as celery_control
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from uuslug import uuslug

from remo.reports.tasks import send_remo_mail


class Poll(models.Model):
    """Poll Model."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()
    valid_groups = models.ForeignKey(Group, related_name='valid_polls')
    created_on = models.DateField(auto_now_add=True)
    description = models.TextField(validators=[MaxLengthValidator(500),
                                               MinLengthValidator(20)])
    created_by = models.ForeignKey(User, related_name='range_polls_created')
    users_voted = models.ManyToManyField(User, related_name='polls_voted',
                                         through='Vote')
    task_start_id = models.CharField(max_length=256, blank=True,
                                     null=True, editable=False)
    task_end_id = models.CharField(max_length=256, blank=True, null=True,
                                   editable=False)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['-created_on']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.slug = uuslug(self.name, instance=self)
        super(Poll, self).save(*args, **kwargs)


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
    nominee = models.ForeignKey(User)

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


@receiver(pre_save, sender=Poll,
          dispatch_uid='voting_poll_email_reminder_signal')
def poll_email_reminder(sender, instance, **kwargs):
    """Set an email reminder when a voting starts."""
    subject_start = '[Voting] Cast your vote for %s now!' % instance.name
    subject_end = '[Voting] Results for %s' % instance.name

    start_voting_template = 'emails/voting_starting_reminder.txt'
    end_voting_template = 'emails/voting_results_reminder.txt'

    recipients = User.objects.filter(
        groups=instance.valid_groups).distinct()
    ctx_data = {'poll': instance}
    start_reminder = send_remo_mail.apply_async(args=[recipients,
                                                      subject_start,
                                                      start_voting_template,
                                                      ctx_data],
                                                eta=instance.start)
    end_reminder = send_remo_mail.apply_async(args=[recipients,
                                                    subject_end,
                                                    end_voting_template,
                                                    ctx_data],
                                              eta=instance.end)
    instance.task_start_id = start_reminder.task_id
    instance.task_end_id = end_reminder.task_id


@receiver(pre_delete, sender=Poll,
          dispatch_uid='voting_poll_delete_reminder_signal')
def poll_delete_reminder(sender, instance, **kwargs):
    if instance.task_start_id:
        celery_control.revoke(instance.task_start_id)
    if instance.task_end_id:
        celery_control.revoke(instance.task_end_id)
