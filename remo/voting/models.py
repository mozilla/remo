from datetime import timedelta

from django.core.urlresolvers import reverse
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now

from django_statsd.clients import statsd
from uuslug import uuslug

from remo.base.tasks import send_remo_mail
from remo.celery import app as celery_app
from remo.dashboard.models import ActionItem, Item
from remo.remozilla.models import Bug
from remo.remozilla.utils import get_bugzilla_url
from remo.voting.tasks import send_voting_mail


# Voting period in days
BUDGET_REQUEST_PERIOD_START = 3
BUDGET_REQUEST_PERIOD_END = 6
VOTE_ACTION = 'Cast your vote for'
BUDGET_VOTE_ACTION = 'Cast your vote for budget request'


@python_2_unicode_compatible
class Poll(models.Model):
    """Poll Model."""
    name = models.CharField(max_length=300)
    slug = models.SlugField(blank=True, max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()
    valid_groups = models.ForeignKey(Group, related_name='valid_polls')
    created_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField(validators=[MaxLengthValidator(2500),
                                               MinLengthValidator(20)])
    created_by = models.ForeignKey(User, related_name='range_polls_created')
    users_voted = models.ManyToManyField(User, related_name='polls_voted',
                                         through='Vote')
    task_start_id = models.CharField(max_length=256, blank=True,
                                     null=True, editable=False, default='')
    task_end_id = models.CharField(max_length=256, blank=True, null=True,
                                   editable=False, default='')
    bug = models.ForeignKey(Bug, null=True, blank=True)
    automated_poll = models.BooleanField(default=False)
    comments_allowed = models.BooleanField(default=True)
    is_extended = models.BooleanField(default=False)
    action_items = generic.GenericRelation(ActionItem)

    def get_absolute_url(self):
        return reverse('remo.voting.views.view_voting',
                       args=[self.slug])

    @property
    def is_future_voting(self):
        if self.start > now():
            return True
        return False

    @property
    def is_current_voting(self):
        if self.start < now() and self.end > now():
            return True
        return False

    @property
    def is_past_voting(self):
        if self.end < now():
            return True
        return False

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_on']

    def save(self, *args, **kwargs):
        """Custom save method."""

        create_action_items = False

        if not self.pk:
            self.slug = uuslug(self.name, instance=self)
            create_action_items = True
        else:
            # Update action items
            current_poll = Poll.objects.get(id=self.pk)
            action_model = ContentType.objects.get_for_model(self)
            action_items = ActionItem.objects.filter(content_type=action_model,
                                                     object_id=self.pk)

            if current_poll.end != self.end:
                action_items.update(due_date=self.end.date())

            if current_poll.valid_groups != self.valid_groups:
                action_items.delete()
                create_action_items = True

            if not settings.CELERY_ALWAYS_EAGER:
                if self.is_current_voting:
                    celery_app.control.revoke(self.task_end_id)
                elif self.is_future_voting:
                    celery_app.control.revoke(self.task_start_id)
                    celery_app.control.revoke(self.task_end_id)

            if not self.is_future_voting:
                obj = Poll.objects.get(pk=self.id)
                if self.end > obj.end:
                    self.is_extended = True

        super(Poll, self).save()

        if create_action_items:
            ActionItem.create(self)

    def get_action_items(self):
        action_items = []
        due_date = self.end.date()

        if self.automated_poll:
            name = u'{0} {1}'.format(BUDGET_VOTE_ACTION, self.bug.summary)
            priority = ActionItem.MAJOR
        else:
            name = u'{0} {1}'.format(VOTE_ACTION, self.name)
            priority = ActionItem.NORMAL

        # Exclude the users that already have voted
        users = (User.objects.filter(groups=self.valid_groups)
                 .exclude(pk__in=self.vote_set.values_list('user',
                                                           flat=True)))
        for user in users:
            action_item = Item(name, user, priority, due_date)
            action_items.append(action_item)

        return action_items


@python_2_unicode_compatible
class Vote(models.Model):
    """Vote model."""
    user = models.ForeignKey(User, related_name='votes')
    poll = models.ForeignKey(Poll)
    date_voted = models.DateField(auto_now_add=True)

    def __str__(self):
        return u'{0} {1}'.format(self.user, self.poll)

    def save(self, *args, **kwargs):
        if self.poll.automated_poll:
            name = u'{0} {1}'.format(BUDGET_VOTE_ACTION, self.poll.bug.summary)
        else:
            name = u'{0} {1}'.format(VOTE_ACTION, self.poll.name)

        super(Vote, self).save(*args, **kwargs)
        ActionItem.resolve(instance=self.poll, user=self.user,
                           name=name)


@python_2_unicode_compatible
class RangePoll(models.Model):
    """Range Poll Model."""
    name = models.CharField(max_length=500, default='')
    poll = models.ForeignKey(Poll, related_name='range_polls')

    def __str__(self):
        return self.name


class RangePollChoice(models.Model):
    """Range Poll Choice Model."""
    votes = models.IntegerField(default=0)
    range_poll = models.ForeignKey(RangePoll, related_name='choices')
    nominee = models.ForeignKey(User, limit_choices_to={'groups__name': 'Rep'})

    class Meta:
        ordering = ['nominee__first_name', 'nominee__last_name']


@python_2_unicode_compatible
class RadioPoll(models.Model):
    """Radio Poll Model."""
    question = models.CharField(max_length=500)
    poll = models.ForeignKey(Poll, related_name='radio_polls')

    def __str__(self):
        return self.question


@python_2_unicode_compatible
class RadioPollChoice(models.Model):
    """Radio Poll Choice Model."""
    answer = models.CharField(max_length=500)
    votes = models.IntegerField(default=0)
    radio_poll = models.ForeignKey(RadioPoll, related_name='answers')

    def __str__(self):
        return self.answer

    class Meta:
        ordering = ['radio_poll__question']


class PollComment(models.Model):
    """Comments in Poll."""
    user = models.ForeignKey(User)
    poll = models.ForeignKey(Poll, related_name='comments')
    created_on = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()

    def get_absolute_delete_url(self):
        return reverse('remo.voting.views.delete_poll_comment',
                       args=[self.poll.slug,
                             self.user.userprofile.display_name,
                             self.id])

    class Meta:
        ordering = ['created_on']


@receiver(post_save, sender=Poll,
          dispatch_uid='voting_poll_email_reminder_signal')
def poll_email_reminder(sender, instance, raw, **kwargs):
    """Send email reminders when a vote starts/ends."""
    subject_start = '[Voting] Cast your vote for "%s" now!' % instance.name
    subject_end = '[Voting] Results for "%s"' % instance.name

    start_template = 'emails/voting_starting_reminder.jinja'
    end_template = 'emails/voting_results_reminder.jinja'
    task_start_id = ''
    task_end_id = ''

    if not instance.task_start_id or instance.is_future_voting:
        start_reminder = send_voting_mail.apply_async(
            eta=instance.start, kwargs={'voting_id': instance.id,
                                        'subject': subject_start,
                                        'email_template': start_template})
        task_start_id = start_reminder.task_id
    end_reminder = send_voting_mail.apply_async(
        eta=instance.end, kwargs={'voting_id': instance.id,
                                  'subject': subject_end,
                                  'email_template': end_template})
    task_end_id = end_reminder.task_id
    Poll.objects.filter(pk=instance.pk).update(task_start_id=task_start_id,
                                               task_end_id=task_end_id)


@receiver(post_save, sender=Poll,
          dispatch_uid='voting_automated_poll_discussion_email')
def automated_poll_discussion_email(sender, instance, created, raw, **kwargs):
    """Send email reminders when a vote starts/ends."""
    if instance.automated_poll and created:
        template = 'emails/review_budget_notify_council.jinja'
        subject = (u'Discuss [Bug {id}] - {summary}'
                   .format(id=instance.bug.bug_id,
                           summary=unicode(instance.bug.summary)))
        data = {'bug': instance.bug,
                'BUGZILLA_URL': get_bugzilla_url(instance.bug),
                'poll': instance}
        send_remo_mail.delay(
            subject=subject, email_template=template,
            recipients_list=[settings.REPS_COUNCIL_ALIAS],
            data=data)


@receiver(pre_delete, sender=Poll,
          dispatch_uid='voting_poll_delete_reminder_signal')
def poll_delete_reminder(sender, instance, **kwargs):
    """Revoke the task if a voting is deleted."""
    if not settings.CELERY_ALWAYS_EAGER:
        if instance.task_start_id:
            celery_app.control.revoke(instance.task_start_id)
        if instance.task_end_id:
            celery_app.control.revoke(instance.task_end_id)


@receiver(post_save, sender=Bug,
          dispatch_uid='remozilla_automated_poll_signal')
def automated_poll(sender, instance, **kwargs):
    """Create a radio poll automatically.

    If a bug lands in our database with council_vote_requested, create
    a new Poll and let Council members vote.

    """
    if ((not instance.council_vote_requested or
         Poll.objects.filter(bug=instance).exists())):
        return

    remobot = User.objects.get(username='remobot')

    with transaction.atomic():
        poll = (Poll.objects
                .create(name=instance.summary,
                        description=instance.first_comment,
                        valid_groups=Group.objects.get(name='Council'),
                        start=(now() +
                               timedelta(BUDGET_REQUEST_PERIOD_START)),
                        end=(now() +
                             timedelta(days=BUDGET_REQUEST_PERIOD_END)),
                        bug=instance,
                        created_by=remobot,
                        automated_poll=True))

        radio_poll = RadioPoll.objects.create(poll=poll,
                                              question='Budget Approval')

        RadioPollChoice.objects.create(answer='Approved',
                                       radio_poll=radio_poll)
        RadioPollChoice.objects.create(answer='Denied', radio_poll=radio_poll)

        statsd.incr('voting.create_automated_poll')


@receiver(post_save, sender=PollComment,
          dispatch_uid='voting_email_commenters_on_add_poll_comment_signal')
def email_commenters_on_add_poll_comment(sender, instance, **kwargs):
    """Email a user when a comment is added to a poll."""
    poll = instance.poll
    if poll.comments_allowed:
        subject = '[Voting] User {0} commented on {1}'
        email_template = 'emails/user_notification_on_add_poll_comment.jinja'

        # Send an email to all users commented so far on the poll except from
        # the user who made the comment. Dedup the list with unique IDs.
        commenters = set(PollComment.objects.filter(poll=poll)
                         .exclude(user=instance.user)
                         .values_list('user', flat=True))

        # Add the creator of the poll in the list
        if poll.created_by.id not in commenters:
            commenters.add(poll.created_by.id)

        for user_id in commenters:
            user = User.objects.get(pk=user_id)
            if (user.userprofile.receive_email_on_add_voting_comment and
                    user != instance.user):
                ctx_data = {'poll': poll, 'user': user,
                            'commenter': instance.user,
                            'comment': instance.comment,
                            'created_on': instance.created_on}
                subject = subject.format(instance.user.get_full_name(), poll)
                send_remo_mail.delay(subject=subject,
                                     recipients_list=[user_id],
                                     email_template=email_template,
                                     data=ctx_data)
