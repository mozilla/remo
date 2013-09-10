from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import utc

import caching.base


class Bug(caching.base.CachingMixin, models.Model):
    """Bug model definition."""
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    bug_id = models.PositiveIntegerField()
    bug_creation_time = models.DateTimeField(blank=True, null=True)
    bug_last_change_time = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(User, null=True, blank=True,
                                related_name='bugs_created',
                                on_delete=models.SET_NULL)
    assigned_to = models.ForeignKey(User, null=True, blank=True,
                                    related_name='bugs_assigned',
                                    on_delete=models.SET_NULL)
    cc = models.ManyToManyField(User, related_name='bugs_cced')
    component = models.CharField(max_length=200)
    summary = models.CharField(max_length=500, default='')
    whiteboard = models.CharField(max_length=500, default='')
    status = models.CharField(max_length=30, default='')
    resolution = models.CharField(max_length=30, default='')
    due_date = models.DateTimeField(null=True, blank=True)

    objects = caching.base.CachingManager()

    def __unicode__(self):
        return u'%d' % self.bug_id

    class Meta:
        ordering = ['-bug_last_change_time']


class Status(models.Model):
    """Status model definition.

    The status model is expected to have only one entry, that carries
    the time-stamp of the last successful sync with Bugzilla.

    """
    last_updated = models.DateTimeField(default=datetime(1970, 1, 1, 0, 0,
                                                         tzinfo=utc))

    def __unicode__(self):
        return "Last update: %s" % self.last_updated.strftime('%H:%M %d %b %Y')

    class Meta:
        verbose_name_plural = 'statuses'


@receiver(pre_save, sender=Bug, dispatch_uid='set_uppercase_pre_save_signal')
def set_uppercase_pre_save(sender, instance, **kwargs):
    """Convert status and resolution to uppercase prior to saving."""
    if instance.status:
        instance.status = instance.status.upper()
    if instance.resolution:
        instance.resolution = instance.resolution.upper()
