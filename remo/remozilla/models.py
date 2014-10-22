from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import m2m_changed, pre_save
from django.dispatch import receiver
from django.utils.timezone import utc

import caching.base

from remo.dashboard.models import ActionItem, Item


ADD_RECEIPTS_ACTION = 'Add receipts to bug'
ADD_REPORT_ACTION = 'Add report to bug'
ADD_PHOTOS_ACTION = 'Add photos to bug'
ADD_REPORTS_PHOTOS_ACTION = 'Add reports/photos to bug'
REVIEW_BUDGET_REQUEST_ACTION = 'Review budget request bug'
WAITING_MENTOR_VALIDATION_ACTION = 'Waiting mentor validation'
NEEDINFO_ACTION = 'Pending open questions'


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
        # Avoid circular dependency
        from remo.base.helpers import user_is_rep

        if not self.assigned_to or not user_is_rep(self.assigned_to):
            return []

        action_items = []
        names = [
            (ADD_RECEIPTS_ACTION, 'waiting_receipts', ActionItem.NORMAL),
            (ADD_REPORT_ACTION, 'waiting_report', ActionItem.NORMAL),
            (ADD_PHOTOS_ACTION, 'waiting_photos', ActionItem.NORMAL),
            (ADD_REPORTS_PHOTOS_ACTION,
             'waiting_report_photos', ActionItem.NORMAL),
            (REVIEW_BUDGET_REQUEST_ACTION,
             'council_member_assigned', ActionItem.BLOCKER)
        ]

        for action_name, attr, priority in names:
            if getattr(self, attr, None):
                action_item = Item(action_name, self.assigned_to,
                                   priority, None)
                action_items.append(action_item)
            else:
                ActionItem.resolve(instance=self, user=self.assigned_to,
                                   name=action_name)

        action_name = WAITING_MENTOR_VALIDATION_ACTION
        if self.assigned_to and user_is_rep(self.assigned_to):
            mentor = self.assigned_to.userprofile.mentor
            if self.pending_mentor_validation:
                action_item = Item(action_name, mentor,
                                   ActionItem.BLOCKER, None)
                action_items.append(action_item)
            else:
                ActionItem.resolve(instance=self, user=mentor,
                                   name=action_name)

        action_name = NEEDINFO_ACTION
        for user in self.budget_needinfo.all():
            action_item = Item(action_name, user, ActionItem.CRITICAL, None)
            action_items.append(action_item)

        return action_items

    def save(self, *args, **kwargs):
        # Update action items
        action_model = ContentType.objects.get_for_model(self)
        if self.pk:
            names = [ADD_RECEIPTS_ACTION, ADD_REPORT_ACTION,
                     ADD_PHOTOS_ACTION, ADD_REPORTS_PHOTOS_ACTION,
                     REVIEW_BUDGET_REQUEST_ACTION]

            current_bug = Bug.objects.get(id=self.pk)
            action_items = ActionItem.objects.filter(content_type=action_model,
                                                     object_id=self.pk)

            if current_bug.assigned_to != self.assigned_to:
                items = action_items.filter(name__in=names)
                items.update(user=self.assigned_to)

            try:
                current_mentor = current_bug.assigned_to.userprofile.mentor
                new_mentor = self.assigned_to.userprofile.mentor
            except AttributeError:
                current_mentor = None
                new_mentor = None

            if current_mentor != new_mentor:
                action_name = WAITING_MENTOR_VALIDATION_ACTION
                items = action_items.filter(name=action_name)
                items.update(user=new_mentor)

        super(Bug, self).save(*args, **kwargs)

        if self.status == 'RESOLVED':
            items = ActionItem.objects.filter(content_type=action_model,
                                              object_id=self.pk)
            items.update(resolved=True)

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
    name = 'Pending open questions'
    if action == 'post_remove':
        for pk in pk_set:
            ActionItem.resolve(instance=instance, user=User.objects.get(pk=pk),
                               name=name)

    if action == 'post_clear':
        for user in instance.budget_needinfo.all():
            ActionItem.resolve(instance=instance, user=user, name=name)

    if action == 'post_add':
        ActionItem.create(instance=instance)
