from datetime import timedelta

from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.dispatch import receiver
from django.utils.timezone import now

from remo.base.tasks import send_remo_mail
from remo.celery import app as celery_app
from remo.remozilla.models import Bug
from remo.remozilla.utils import get_bugzilla_url
from remo.voting.models import Poll, PollComment, RadioPoll, RadioPollChoice
from remo.voting.tasks import send_voting_mail

# Voting period in days
BUDGET_REQUEST_PERIOD_START = 3
BUDGET_REQUEST_PERIOD_END = 6
VOTE_ACTION = 'Cast your vote for'
BUDGET_VOTE_ACTION = 'Cast your vote for budget request'


@receiver(post_save, sender=Poll, dispatch_uid='voting_poll_email_reminder_signal')
def poll_email_reminder(sender, instance, raw, **kwargs):
    """Send email reminders when a vote starts/ends."""
    subject_start = '[Voting] Cast your vote for "%s" now!' % instance.name
    subject_end = '[Voting] Results for "%s"' % instance.name

    start_template = 'emails/voting_starting_reminder.jinja'
    end_template = 'emails/voting_results_reminder.jinja'

    if not instance.task_start_id or instance.is_future_voting:
        start_reminder = send_voting_mail.apply_async(
            eta=instance.start, kwargs={'voting_id': instance.id,
                                        'subject': subject_start,
                                        'email_template': start_template})
        Poll.objects.filter(pk=instance.pk).update(task_start_id=start_reminder.task_id)
    if not instance.task_end_id:
        end_reminder = send_voting_mail.apply_async(
            eta=instance.end, kwargs={'voting_id': instance.id,
                                      'subject': subject_end,
                                      'email_template': end_template})
        Poll.objects.filter(pk=instance.pk).update(task_end_id=end_reminder.task_id)


@receiver(post_save, sender=Poll, dispatch_uid='voting_automated_poll_discussion_email')
def automated_poll_discussion_email(sender, instance, created, raw, **kwargs):
    """Send email reminders when a vote starts/ends."""
    if instance.automated_poll and created:
        template = 'emails/review_budget_notify_review_team.jinja'
        subject = u'Discuss [Bug {id}] - {summary}'.format(id=instance.bug.bug_id,
                                                           summary=unicode(instance.bug.summary))
        data = {'bug': instance.bug,
                'BUGZILLA_URL': get_bugzilla_url(instance.bug),
                'poll': instance}
        send_remo_mail.delay(
            subject=subject, email_template=template,
            recipients_list=[settings.REPS_REVIEW_ALIAS],
            data=data)


@receiver(pre_delete, sender=Poll,
          dispatch_uid='voting_poll_delete_reminder_signal')
def poll_delete_reminder(sender, instance, **kwargs):
    """Revoke the task if a voting is deleted."""
    if not settings.CELERY_TASK_ALWAYS_EAGER:
        if instance.task_start_id:
            celery_app.control.revoke(instance.task_start_id)
        if instance.task_end_id:
            celery_app.control.revoke(instance.task_end_id)


@receiver(post_save, sender=Bug, dispatch_uid='remozilla_automated_poll_signal')
def automated_poll(sender, instance, **kwargs):
    """Create a radio poll automatically.

    If a bug lands in our database with council_vote_requested, create
    a new Poll and let Review members vote.

    """
    if not instance.council_vote_requested or Poll.objects.filter(bug=instance).exists():
        return

    remobot = User.objects.get(username='remobot')

    with transaction.atomic():
        poll = (Poll.objects.create(name=instance.summary,
                                    description=instance.first_comment,
                                    valid_groups=Group.objects.get(name='Review'),
                                    start=now() + timedelta(BUDGET_REQUEST_PERIOD_START),
                                    end=now() + timedelta(days=BUDGET_REQUEST_PERIOD_END),
                                    bug=instance,
                                    created_by=remobot,
                                    automated_poll=True))

        radio_poll = RadioPoll.objects.create(poll=poll, question='Budget Approval')

        RadioPollChoice.objects.create(answer='Approved', radio_poll=radio_poll)
        RadioPollChoice.objects.create(answer='Denied', radio_poll=radio_poll)


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
            if (user.userprofile.receive_email_on_add_voting_comment and user != instance.user):
                ctx_data = {'poll': poll, 'user': user,
                            'commenter': instance.user,
                            'comment': instance.comment,
                            'created_on': instance.created_on}
                subject = subject.format(instance.user.get_full_name(), poll)
                send_remo_mail.delay(subject=subject,
                                     recipients_list=[user_id],
                                     email_template=email_template,
                                     data=ctx_data)
