from django.apps import apps
from django.contrib.auth.models import User
from django.db.models.signals import m2m_changed, pre_save
from django.dispatch import receiver

from remo.remozilla.models import Bug


ActionItem = apps.get_model('dashboard', 'ActionItem')

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
