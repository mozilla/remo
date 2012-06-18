import datetime

from django.contrib.auth.models import Group, User, Permission
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from south.signals import post_migrate

from remo.base.utils import go_back_n_months

OVERDUE_DAY = 7


class Report(models.Model):
    """Report Model."""
    user = models.ForeignKey(User, related_name='reports')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    mentor = models.ForeignKey(User, null=True, default=None,
                               related_name='reports_mentored')
    month = models.DateField()
    empty = models.BooleanField(default=False)
    recruits_comments = models.TextField(blank=True, default='')
    past_items = models.TextField(blank=True, default='')
    future_items = models.TextField(blank=True, default='')
    flags = models.TextField(blank=True, default='')
    overdue = models.BooleanField(default=False)

    class Meta:
        ordering=['-month']
        unique_together = ['user', 'month']
        permissions = [('can_edit_reports', 'Can edit reports'),
                       ('can_delete_reports', 'Can delete reports')]

    def __unicode__(self):
        return self.month.strftime('%b %Y')


@receiver(post_migrate)
def report_set_groups(app, sender, signal, **kwargs):
    """Set permissions to groups."""
    if (isinstance(app, basestring) and app != 'reports'):
        return True

    for group_name in ['Admin', 'Mentor']:
        for perm in ['can_edit_reports', 'can_delete_reports']:
            group, created = Group.objects.get_or_create(name=group_name)
            permission = Permission.objects.get(codename=perm,
                                                content_type__name='report')
            group.permissions.add(permission)


@receiver(pre_save, sender=Report)
def report_set_mentor_pre_save(sender, instance, raw, **kwargs):
    """Set mentor from UserProfile only on first save."""
    if not instance.id and not raw:
        instance.mentor = instance.user.userprofile.mentor


@receiver(pre_save, sender=Report)
def report_set_month_day_pre_save(sender, instance, **kwargs):
    """Set month day to the first day of the month."""
    instance.month = datetime.datetime(year=instance.month.year,
                                       month=instance.month.month, day=1)


@receiver(pre_save, sender=Report)
def report_set_overdue_pre_save(sender, instance, raw, **kwargs):
    """Set overdue on Report object creation."""
    today = datetime.date.today()
    previous_month = go_back_n_months(today, first_day=True)

    if not instance.id and not raw:
        if (previous_month > instance.month or
            (previous_month == instance.month and today.day > OVERDUE_DAY)):
            instance.overdue = True


class ReportComment(models.Model):
    """Comments in Report."""
    user = models.ForeignKey(User)
    report = models.ForeignKey(Report)
    created_on = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()

    class Meta:
        ordering = ['id']


class ReportEvent(models.Model):
    """Event in Report Model."""
    report = models.ForeignKey(Report)
    name = models.CharField(max_length=300)
    description = models.TextField(default='')
    link = models.URLField(max_length=500)
    participation_type = models.PositiveSmallIntegerField(
        choices=((1, 'Organizer'),
                 (2, 'Mozilla presence Organizer'),
                 (3, 'Attendee')))


class ReportLink(models.Model):
    """Link in Reports Model."""
    report = models.ForeignKey(Report)
    description = models.CharField(max_length=500)
    link = models.URLField()
