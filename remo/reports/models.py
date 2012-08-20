import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from south.signals import post_migrate

from remo.base.utils import (add_permissions_to_groups,
                             get_object_or_none, go_back_n_months)
from remo.events.helpers import get_attendee_role_event
from remo.events.models import Attendance as EventAttendance


OVERDUE_DAY = 7
PARTICIPATION_TYPE_CHOICES = ((1, 'Organizer'),
                              (2, 'Mozilla\'s presence organizer'),
                              (3, 'Rep attendee'))


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
        permissions = (('can_edit_reports', 'Can edit reports'),
                       ('can_delete_reports', 'Can delete reports'),
                       ('can_delete_report_comments',
                        'Can delete report comment'))

    def __unicode__(self):
        return self.month.strftime('%b %Y')


@receiver(post_migrate)
def report_set_groups(app, sender, signal, **kwargs):
    """Set permissions to groups."""
    if (isinstance(app, basestring) and app != 'reports'):
        return True

    perms = {'can_edit_reports': ['Admin', 'Mentor'],
             'can_delete_reports': ['Admin', 'Mentor'],
             'can_delete_report_comments': ['Admin', 'Mentor']}

    add_permissions_to_groups('reports', perms)


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


@receiver(post_save, sender=EventAttendance)
def report_add_event(sender, instance, raw, **kwargs):
    """Add event to report."""
    if raw or not instance.user.groups.filter(name='Rep').exists():
        return

    date = datetime.datetime(year=instance.event.end.year,
                             month=instance.event.end.month,
                             day=1)
    report, created = Report.objects.get_or_create(user=instance.user,
                                                   month=date)
    link = (settings.SITE_URL +
            reverse('events_view_event', kwargs={'slug': instance.event.slug}))

    # Import here to avoid circular dependencies.
    from utils import participation_type_to_number
    participation_type = participation_type_to_number(
        get_attendee_role_event(instance.user, instance.event))

    report_event = get_object_or_none(ReportEvent, report=report, link=link)
    if not report_event:
        report_event = ReportEvent(report=report, link=link,
                                   name=instance.event.name,
                                   description=instance.event.description)

    report_event.participation_type = participation_type
    report_event.save()


@receiver(pre_delete, sender=EventAttendance)
def report_remove_event(sender, instance, **kwargs):
    """Remove event from report."""
    date = datetime.datetime(year=instance.event.end.year,
                             month=instance.event.end.month, day=1)
    report = get_object_or_none(Report, user=instance.user, month=date)
    link = (settings.SITE_URL +
            reverse('events_view_event', kwargs={'slug': instance.event.slug}))

    if report:
        report.reportevent_set.filter(link=link).delete()


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
        choices=PARTICIPATION_TYPE_CHOICES)

    # class Meta:
    #     unique_together = ['report', 'link']

class ReportLink(models.Model):
    """Link in Reports Model."""
    report = models.ForeignKey(Report)
    description = models.CharField(max_length=500)
    link = models.URLField()
