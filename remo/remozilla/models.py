from datetime import datetime

from django.db.models.loading import get_model
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import m2m_changed, pre_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import utc


ADD_RECEIPTS_ACTION = u'Add receipts for'
ADD_REPORT_ACTION = u'Add report for'
ADD_PHOTOS_ACTION = u'Add photos for'
ADD_REPORTS_PHOTOS_ACTION = u'Add reports/photos for'
REVIEW_BUDGET_REQUEST_ACTION = u'Review budget request'
WAITING_MENTOR_VALIDATION_ACTION = u'Waiting mentor validation for'
NEEDINFO_ACTION = u'Need info for'
BUG_ATTRS = ['waiting_receipts', 'waiting_report',
             'waiting_photos', 'waiting_report_photos',
             'council_member_assigned',
             'pending_mentor_validation']


def _get_action_name(action_name, instance):
    return u'{0} {1}'.format(action_name, instance.summary)


@python_2_unicode_compatible
class Bug(models.Model):
    """Bug model definition."""
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    bug_id = models.PositiveIntegerField(unique=True)
    bug_creation_time = models.DateTimeField(blank=True, null=True)
    bug_last_change_time = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(User, null=True, blank=True, related_name='bugs_created',
                                on_delete=models.SET_NULL)
    assigned_to = models.ForeignKey(User, null=True, blank=True, related_name='bugs_assigned',
                                    on_delete=models.SET_NULL)
    cc = models.ManyToManyField(User, related_name='bugs_cced')
    component = models.CharField(max_length=200)
    summary = models.CharField(max_length=500, default='')
    whiteboard = models.CharField(max_length=500, default='')
    status = models.CharField(max_length=30, default='')
    resolution = models.CharField(max_length=30, default='')
    first_comment = models.TextField(default='', blank=True)
    # this is now assigned to the review group
    council_vote_requested = models.BooleanField(default=False)
    council_member_assigned = models.BooleanField(default=False)
    pending_mentor_validation = models.BooleanField(default=False)
    budget_needinfo = models.ManyToManyField(User)
    action_items = generic.GenericRelation('dashboard.ActionItem')

    def __str__(self):
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
        from remo.base.templatetags.helpers import user_is_rep
        from remo.dashboard.models import Item
        ActionItem = get_model('dashboard', 'ActionItem')

        if not self.assigned_to or not user_is_rep(self.assigned_to):
            return []

        action_items = []
        actions = [
            (_get_action_name(ADD_RECEIPTS_ACTION, self),
             'waiting_receipts', ActionItem.NORMAL),
            (_get_action_name(ADD_REPORT_ACTION, self),
             'waiting_report', ActionItem.NORMAL),
            (_get_action_name(ADD_PHOTOS_ACTION, self),
             'waiting_photos', ActionItem.NORMAL),
            (_get_action_name(ADD_REPORTS_PHOTOS_ACTION, self),
             'waiting_report_photos', ActionItem.NORMAL),
            (_get_action_name(REVIEW_BUDGET_REQUEST_ACTION, self),
             'council_member_assigned', ActionItem.BLOCKER)
        ]

        for action_name, attr, priority in actions:
            if getattr(self, attr, None):
                action_item = Item(action_name, self.assigned_to, priority, None)
                action_items.append(action_item)

        mentor_action = _get_action_name(WAITING_MENTOR_VALIDATION_ACTION, self)
        if self.assigned_to and user_is_rep(self.assigned_to):
            mentor = self.assigned_to
            if self.pending_mentor_validation:
                action_item = Item(mentor_action, mentor, ActionItem.BLOCKER, None)
                action_items.append(action_item)

        action_name = _get_action_name(NEEDINFO_ACTION, self)
        for user in self.budget_needinfo.all():
            action_item = Item(action_name, user, ActionItem.CRITICAL, None)
            action_items.append(action_item)

        return action_items

    def save(self, *args, **kwargs):
        # Avoid circular dependency
        from remo.base.templatetags.helpers import user_is_rep
        ActionItem = get_model('dashboard', 'ActionItem')

        # Update action items
        action_model = ContentType.objects.get_for_model(self)
        if self.pk:
            # Get saved action item
            action_items = ActionItem.objects.filter(content_type=action_model,
                                                     object_id=self.pk,
                                                     resolved=False)
            # If there is no user or user is not rep or the bug is resolved,
            # resolve the action item too!
            if (not self.assigned_to or not user_is_rep(self.assigned_to) or
                    self.status == 'RESOLVED'):
                action_items.update(resolved=True)
            else:
                possible_actions = [ADD_RECEIPTS_ACTION, ADD_REPORT_ACTION,
                                    ADD_PHOTOS_ACTION,
                                    ADD_REPORTS_PHOTOS_ACTION,
                                    REVIEW_BUDGET_REQUEST_ACTION,
                                    WAITING_MENTOR_VALIDATION_ACTION]
                action_names = ([u'{0} {1}'.format(action, self.summary)
                                 for action in possible_actions])
                # Resolve any non-valid action items.
                invalid_actions = []
                for action_name, attr in zip(action_names, BUG_ATTRS):
                    if not getattr(self, attr):
                        invalid_actions.append(action_name)
                invalid_action_items = action_items.filter(name__in=invalid_actions)
                for invalid_item in invalid_action_items:
                    ActionItem.resolve(self, invalid_item.user, invalid_item.name)

                # If the bug changed owner, re-assign it
                current_bug = Bug.objects.get(id=self.pk)
                if current_bug.assigned_to != self.assigned_to:
                    action_items.filter(name__in=action_names).update(user=self.assigned_to)

        super(Bug, self).save()

    class Meta:
        ordering = ['-bug_last_change_time']


@python_2_unicode_compatible
class Status(models.Model):
    """Status model definition.

    The status model is expected to have only one entry, that carries
    the time-stamp of the last successful sync with Bugzilla.

    """
    last_updated = models.DateTimeField(default=datetime(1970, 1, 1, 0, 0, tzinfo=utc))

    def __str__(self):
        return u'Last update: %s' % self.last_updated.strftime('%H:%M %d %b %Y')

    class Meta:
        verbose_name_plural = 'statuses'


@receiver(pre_save, sender=Bug, dispatch_uid='set_uppercase_pre_save_signal')
def set_uppercase_pre_save(sender, instance, **kwargs):
    """Convert status and resolution to uppercase prior to saving."""
    if instance.status:
        instance.status = instance.status.upper()
    if instance.resolution:
        instance.resolution = instance.resolution.upper()


@receiver(m2m_changed, sender=Bug.budget_needinfo.through, dispatch_uid='update_needinfo_signal')
def update_budget_needinfo_action_items(sender, instance, action, pk_set, **kwargs):
    """Update ActionItem objects on needinfo change."""

    ActionItem = get_model('dashboard', 'ActionItem')
    name = u'{0} {1}'.format(NEEDINFO_ACTION, instance.summary)
    if action == 'post_remove':
        for pk in pk_set:
            ActionItem.resolve(instance=instance, user=User.objects.get(pk=pk), name=name)

    if action == 'pre_clear':
        for user in instance.budget_needinfo.all():
            ActionItem.resolve(instance=instance, user=user, name=name)

    if action == 'post_add':
        ActionItem.create(instance=instance)
