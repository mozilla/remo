from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save


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

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-due_date', '-updated_on', '-created_on']

    def __unicode__(self):
        return self.action_type


def create_action_items(sender, instance, **kwargs):
    action_model = ContentType.objects.get_for_model(instance)
    action_items = ActionItem.objects.filter(content_type__pk=action_model.id,
                                             object_id=instance.id)

    for (action_type, user, priority, due_date) in instance.get_action_items():
        if not action_items.filter(action_type=action_type,
                                   user=user, completed=False).exists():
            args = {
                'content_object': instance,
                'action_type': action_type,
                'user': user,
                'priority': priority,
                'due_date': due_date
            }
            item = ActionItem(**args)
            item.save()


from remo.remozilla.models import Bug

post_save.connect(create_action_items, sender=Bug,
                  dispatch_uid='create_action_items_sig')
