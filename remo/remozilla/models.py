from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import utc

import caching.base

from remo.dashboard.models import ActionItem


class Bug(caching.base.CachingMixin, models.Model):
    """Bug model definition."""
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    bug_id = models.PositiveIntegerField(unique=True)
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
    first_comment = models.TextField(default='', blank=True)
    council_vote_requested = models.BooleanField(default=False)
    council_member_assigned = models.BooleanField(default=False)
    pending_mentor_validation = models.BooleanField(default=False)
    budget_needinfo = models.ManyToManyField(User)
    action_items = generic.GenericRelation(ActionItem)

    objects = caching.base.CachingManager()

    def __unicode__(self):
        return u'%d' % self.bug_id

    @property
    def waiting_receipts(self):
        return '[waiting receipts]' in self.whiteboard

    @property
    def waiting_report_photos(self):
        return '[waiting report and photos]' in self.whiteboard

    @property
    def waiting_report(self):
        return '[waiting report]' in self.whiteboard

    @property
    def waiting_photos(self):
        return '[waiting photos]' in self.whiteboard

    def get_action_items(self):
        action_items = []

        action_types = [
            ('Add receipts to bug', 'waiting_receipts', ActionItem.NORMAL),
            ('Add report to bug', 'waiting_report', ActionItem.NORMAL),
            ('Add photos to bug', 'waiting_photos', ActionItem.NORMAL),
            ('Add receipts/photos to bug',
             'waiting_report_photos', ActionItem.NORMAL),
            ('Review budget request bug',
             'council_member_assigned', ActionItem.BLOCKER)
        ]

        # TODO add due dates
        for action_name, attr, priority in action_types:
            if getattr(self, attr, None):
                action_item = (action_name, self.assigned_to,
                               priority, None)
                action_items.append(action_item)

        if self.pending_mentor_validation:
            action_name = 'Waiting mentor validation'
            mentor = self.assigned_to.userprofile.mentor
            action_item = (action_name, mentor, ActionItem.BLOCKER, None)
            action_items.append(action_item)

        action_name = 'Pending open questions'
        for user in self.budget_needinfo.all():
            action_item = (action_name, user, ActionItem.CRITICAL, None)
            action_items.append(action_item)

        return action_items

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
