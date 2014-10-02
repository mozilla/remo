from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.db import models
from django.db.models.signals import m2m_changed, pre_save
from django.dispatch import receiver
from django.utils.timezone import utc

import caching.base

from remo.base.helpers import user_is_rep
from remo.dashboard.models import ActionItem, Item
from remo.dashboard.signals import action_item_resolved


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
        if not self.assigned_to:
            return []

        if not user_is_rep(self.assigned_to):
            return []

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
                action_item = Item(action_name, self.assigned_to,
                                   priority, None)
                action_items.append(action_item)
            else:
                action_item_resolved.send(sender=self.__class__,
                                          instance=self,
                                          user=self.assigned_to,
                                          action_type=action_name)

        action_name = 'Waiting mentor validation'
        if self.assigned_to and self.assigned_to.userprofile.mentor:
            mentor = self.assigned_to.userprofile.mentor
            if self.pending_mentor_validation:
                action_item = Item(action_name, mentor,
                                   ActionItem.BLOCKER, None)
                action_items.append(action_item)
            else:
                action_item_resolved.send(sender=self.__class__,
                                          instance=self,
                                          user=mentor,
                                          action_type=action_name)

        action_name = 'Pending open questions'
        for user in self.budget_needinfo.all():
            action_item = Item(action_name, user, ActionItem.CRITICAL, None)
            action_items.append(action_item)

        return action_items

    def save(self, *args, **kwargs):
        old_needinfo = set()

        if self.pk:
            old_needinfo = set(self.budget_needinfo.all())

        super(Bug, self).save(*args, **kwargs)

        new_needinfo = set(self.budget_needinfo.all())

        if not old_needinfo == new_needinfo:
            for user in old_needinfo.difference(new_needinfo):
                action_item_resolved.send(sender=self.__class__,
                                          instance=self,
                                          user=user,
                                          action_type='Pending open questions')

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


@receiver(m2m_changed, sender=Bug.budget_needinfo.through,
          dispatch_uid='update_needinfo_signal')
def update_budget_needinfo_action_items(sender, instance, action, pk_set,
                                        **kwargs):
    """Update ActionItem objects on needinfo change."""
    action_type = 'Pending open questions'
    if action == 'post_remove':
        for pk in pk_set:
            action_item_resolved.send(sender=Bug, instance=instance,
                                      user=User.objects.get(pk=pk),
                                      action_type=action_type)

    if action == 'pre_clear':
        for user in instance.budget_needinfo.all():
            action_item_resolved.send(sender=Bug, instance=instance,
                                      user=user, action_type=action_type)
