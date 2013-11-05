import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

import caching.base
from south.signals import post_migrate

import remo.base.utils as utils
from remo.base.utils import (add_permissions_to_groups,
                             get_object_or_none, go_back_n_months)
from remo.events.models import Attendance as EventAttendance, Event
from remo.profiles.models import FunctionalArea
from remo.reports.tasks import send_remo_mail

# OLD REPORTING SYSTEM
OVERDUE_DAY = 7
PARTICIPATION_TYPE_CHOICES = ((1, 'Organizer'),
                              (2, 'Mozilla\'s presence organizer'),
                              (3, 'Rep attendee'))


class Report(caching.base.CachingMixin, models.Model):
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

    objects = caching.base.CachingManager()

    class Meta:
        ordering = ['-month']
        unique_together = ['user', 'month']
        permissions = (('can_edit_reports', 'Can edit reports'),
                       ('can_delete_reports', 'Can delete reports'),
                       ('can_delete_report_comments',
                        'Can delete report comment'))

    def __unicode__(self):
        return self.month.strftime('%b %Y')


@receiver(post_migrate, dispatch_uid='report_set_groups_signal')
def report_set_groups(app, sender, signal, **kwargs):
    """Set permissions to groups."""
    if (isinstance(app, basestring) and app != 'reports'):
        return True

    perms = {'can_edit_reports': ['Admin', 'Mentor'],
             'can_delete_reports': ['Admin', 'Mentor'],
             'can_delete_report_comments': ['Admin', 'Mentor'],
             'add_ngreport': ['Admin'],
             'change_ngreport': ['Admin'],
             'delete_ngreport': ['Admin']}

    add_permissions_to_groups('reports', perms)


@receiver(pre_save, sender=Report,
          dispatch_uid='report_set_mentor_pre_save_signal')
def report_set_mentor_pre_save(sender, instance, raw, **kwargs):
    """Set mentor from UserProfile only on first save."""
    if not instance.id and not raw:
        instance.mentor = instance.user.userprofile.mentor


@receiver(pre_save, sender=Report,
          dispatch_uid='report_set_month_day_pre_save_signal')
def report_set_month_day_pre_save(sender, instance, **kwargs):
    """Set month day to the first day of the month."""
    instance.month = datetime.datetime(year=instance.month.year,
                                       month=instance.month.month, day=1)


@receiver(pre_save, sender=Report,
          dispatch_uid='report_set_overdue_pre_save_signal')
def report_set_overdue_pre_save(sender, instance, raw, **kwargs):
    """Set overdue on Report object creation."""
    today = datetime.date.today()
    previous_month = go_back_n_months(today, first_day=True)

    if not instance.id and not raw:
        if (previous_month > instance.month
            or (previous_month == instance.month
                and today.day > OVERDUE_DAY)):
            instance.overdue = True


@receiver(post_save, sender=Report,
          dispatch_uid='email_mentor_on_add_report_signal')
def email_mentor_on_add_report(sender, instance, created, **kwargs):
    """Email a mentor when a user adds or edits a report."""
    subject = '[Report] Your mentee, %s %s a report for %s %s.'
    email_template = 'emails/mentor_notification_report_added_or_edited.txt'
    month = instance.month.strftime('%B')
    year = instance.month.strftime('%Y')
    rep_user = instance.user
    rep_profile = instance.user.userprofile
    mentor_profile = instance.mentor.userprofile
    ctx_data = {'rep_user': rep_user, 'rep_profile': rep_profile,
                'new_report': created, 'month': month, 'year': year}
    if created:
        if mentor_profile.receive_email_on_add_report:
            subject = subject % ((rep_profile.display_name,
                                  'added', month, year))
            send_remo_mail.delay([instance.mentor.id], subject, email_template,
                                 ctx_data)
    else:
        if mentor_profile.receive_email_on_edit_report:
            subject = subject % (rep_profile.display_name, 'edited',
                                 month, year)
            send_remo_mail.delay([instance.mentor.id], subject, email_template,
                                 ctx_data)


@receiver(pre_delete, sender=EventAttendance,
          dispatch_uid='report_remove_event_signal')
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


@receiver(post_save, sender=ReportComment,
          dispatch_uid='email_user_on_add_comment_signal')
def email_user_on_add_comment(sender, instance, **kwargs):
    """Email a user when a comment is added to a report."""
    subject = '[Report] User %s commented on your report of %s'
    email_template = 'emails/user_notification_on_add_comment.txt'
    report = instance.report
    owner = instance.report.user
    ctx_data = {'report': report, 'owner': owner, 'user': instance.user,
                'comment': instance.comment, 'created_on': instance.created_on}
    if owner.userprofile.receive_email_on_add_comment:
        subject = subject % (instance.user.get_full_name(),
                             report.month.strftime('%B %Y'))
        send_remo_mail.delay([owner.id], subject, email_template, ctx_data)


class ReportEvent(models.Model):
    """Event in Report Model."""
    report = models.ForeignKey(Report)
    name = models.CharField(max_length=300)
    description = models.TextField(default='')
    link = models.URLField(max_length=500)
    participation_type = models.PositiveSmallIntegerField(
        choices=PARTICIPATION_TYPE_CHOICES)


class ReportLink(models.Model):
    """Link in Reports Model."""
    report = models.ForeignKey(Report)
    description = models.CharField(max_length=500)
    link = models.URLField()


# NEW REPORTING SYSTEM
class GenericActiveManager(models.Manager):
    """
    Generic custom manager used in Activity and Campaign models,
    in order to fetch only the objects marked with an active flag.

    TODO: Reminder to add this manager to FunctionalArea Model
    """
    def get_query_set(self):
        return (super(GenericActiveManager, self).get_query_set()
                .filter(active=True))


class Activity(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    class Meta:
        verbose_name_plural = 'Activities'
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Campaign(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class NGReport(models.Model):
    """ Continuous Reporting Model.

    In order to be able to distinguish the old
    and the new Report models, each model associated
    with the continuous reporting system will have the
    'NG' prefix (NG - New Generation).
    """
    user = models.ForeignKey(User, related_name='ng_reports')
    report_date = models.DateField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    mentor = models.ForeignKey(User, null=True,
                               on_delete=models.SET_NULL,
                               related_name='ng_reports_mentored')
    activity = models.ForeignKey(Activity,
                                 related_name='ng_reports')
    campaign = models.ForeignKey(Campaign, null=True, blank=True,
                                 related_name='ng_reports')
    functional_areas = models.ManyToManyField(
        FunctionalArea, related_name='ng_reports')
    longitude = models.FloatField(blank=False, null=True)
    latitude = models.FloatField(blank=False, null=True)
    location = models.CharField(max_length=150, blank=True, default='')
    is_passive = models.BooleanField(default=False)
    event = models.ForeignKey(Event, null=True, blank=True)
    link = models.URLField(max_length=500, blank=True, default='')
    link_description = models.CharField(max_length=200, blank=True, default='')
    activity_description = models.TextField(blank=True, default='')

    def get_absolute_url(self):
        args = [self.user.userprofile.display_name,
                self.report_date.year,
                utils.number2month(self.report_date.month),
                self.report_date.day,
                str(self.id)]
        return reverse('remo.reports.views.view_ng_report', args=args)

    def get_absolute_edit_url(self):
        args = [self.user.userprofile.display_name,
                self.report_date.year,
                utils.number2month(self.report_date.month),
                self.report_date.day,
                str(self.id)]
        return reverse('remo.reports.views.edit_ng_report', args=args)

    def get_absolute_delete_url(self):
        args = [self.user.userprofile.display_name,
                self.report_date.year,
                utils.number2month(self.report_date.month),
                self.report_date.day,
                str(self.id)]
        return reverse('remo.reports.views.delete_ng_report', args=args)

    class Meta:
        ordering = ['-report_date', '-created_on']

    def __unicode__(self):
        return '%s %s, %s' % (self.report_date,
                              self.created_on.strftime('%H:%M'),
                              self.id)


class NGReportComment(models.Model):
    """Comments in NGReport."""
    user = models.ForeignKey(User)
    report = models.ForeignKey(NGReport)
    created_on = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()

    class Meta:
        ordering = ['id']
