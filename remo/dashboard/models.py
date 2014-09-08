from collections import namedtuple

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save


Item = namedtuple('Item', ['name', 'user', 'priority', 'due_date'])
BUGZILLA_URL = 'https://bugzilla.mozilla.org/show_bug.cgi?id='


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

    name = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES)
    user = models.ForeignKey(User, related_name='action_items_assigned')
    resolved = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def get_absolute_url(self):
        from remo.events.models import Event
        from remo.remozilla.models import Bug
        from remo.reports.models import NGReport
        from remo.voting.models import Poll
        ctype = self.content_type

        if ctype.app_label == 'remozilla' and ctype.model == 'bug':
            bug = Bug.objects.get(pk=self.object_id)
            url = BUGZILLA_URL + '{0}'.format(bug.bug_id)
            return url
        elif ctype.app_label == 'voting' and ctype.model == 'poll':
            poll = Poll.objects.get(pk=self.object_id)
            return poll.get_absolute_url()
        elif ctype.app_label == 'events' and ctype.model == 'event':
            event = Event.objects.get(pk=self.object_id)
            return event.get_absolute_url()
        elif ctype.app_label == 'reports' and ctype.model == 'ngreport':
            report = NGReport.objects.get(pk=self.object_id)
            return report.get_absolute_url()

    class Meta:
        ordering = ['-due_date', '-updated_on', '-created_on']
        unique_together = ('name', 'user', 'object_id')

    def __unicode__(self):
        return self.name

    @staticmethod
    def create(instance, **kwargs):
        for item in instance.get_action_items():
            action_model = ContentType.objects.get_for_model(instance)
            action_items = ActionItem.objects.filter(content_type=action_model,
                                                     object_id=instance.id,
                                                     name=item.name,
                                                     user=item.user)
            if not action_items.exists():
                data = {
                    'content_object': instance,
                    'name': item.name,
                    'user': item.user,
                    'priority': item.priority,
                    'due_date': item.due_date
                }
                item = ActionItem.objects.create(**data)

    @staticmethod
    def resolve(instance, user, name):
        action_model = ContentType.objects.get_for_model(instance)
        action_items = ActionItem.objects.filter(content_type=action_model,
                                                 object_id=instance.id,
                                                 user=user, name=name)
        action_items.update(completed=True, resolved=True)


from remo.remozilla.models import Bug
from remo.voting.models import Poll

post_save.connect(ActionItem.create, sender=Bug,
                  dispatch_uid='create_action_items_bugzilla_sig')
post_save.connect(ActionItem.create, sender=Poll,
                  dispatch_uid='create_action_items_voting_sig')
