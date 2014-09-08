from collections import namedtuple

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save

from remo.dashboard.signals import action_item_resolved


Item = namedtuple('Item', 'name user priority due_date')


class ActionItem(models.Model):
    """ActionItem Model."""
    # List of priorities - borrowed from bugzilla
    MINOR = 1
    NORMAL = 2
    MAJOR = 3
    CRITICAL = 4
    BLOCKER = 5
    PRIORITY_CHOICES = (
        (MINOR, 'Minor'),
        (NORMAL, 'Normal'),
        (MAJOR, 'Major'),
        (CRITICAL, 'Critical'),
        (BLOCKER, 'Blocker'),
    )

    action_type = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES)
    user = models.ForeignKey(User, related_name='action_items_assigned')
    completed = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-due_date', '-updated_on', '-created_on']

    def __unicode__(self):
        return self.action_type


def create_action_items(sender, instance, **kwargs):
    action_model = ContentType.objects.get_for_model(instance)
    action_items = ActionItem.objects.filter(content_type__pk=action_model.id,
                                             object_id=instance.id)

    for item in instance.get_action_items():
        if not action_items.filter(action_type=item.name, user=item.user,
                                   completed=False).exists():
            args = {
                'content_object': instance,
                'action_type': item.name,
                'user': item.user,
                'priority': item.priority,
                'due_date': item.due_date
            }
            item = ActionItem(**args)
            item.save()


def resolve_action_items(sender, instance, **kwargs):
    user = kwargs.get('user')
    action_type = kwargs.get('action_type')
    action_model = ContentType.objects.get_for_model(instance)
    action_items = ActionItem.objects.filter(content_type__pk=action_model.id,
                                             object_id=instance.id, user=user,
                                             action_type=action_type)
    action_items.update(completed=True)


from remo.remozilla.models import Bug

post_save.connect(create_action_items, sender=Bug,
                  dispatch_uid='create_action_items_bugzilla_sig')
action_item_resolved.connect(resolve_action_items, sender=Bug,
                             dispatch_uid='resolve_action_items_bugzilla_sig')
