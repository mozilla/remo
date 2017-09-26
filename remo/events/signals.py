from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.urlresolvers import reverse

from remo.base.tasks import send_remo_mail
from remo.events.models import EventComment


@receiver(post_save, sender=EventComment, dispatch_uid='email_event_owner_on_add_comment_signal')
def email_event_owner_on_add_comment(sender, instance, **kwargs):
    """Email event owner when a comment is added to event."""

    subject = '[Event] User %s commented on event "%s"'
    email_template = 'email/owner_notification_on_add_comment.jinja'
    event = instance.event
    owner = instance.event.owner
    event_url = reverse('events_view_event', kwargs={'slug': event.slug})
    ctx_data = {'event': event, 'owner': owner, 'user': instance.user,
                'comment': instance.comment, 'event_url': event_url}
    if owner.userprofile.receive_email_on_add_event_comment:
        subject = subject % (instance.user.get_full_name(), instance.event.name)
        send_remo_mail.delay(subject=subject, recipients_list=[owner.id],
                             email_template=email_template, data=ctx_data)
