import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import (m2m_changed, post_save, pre_delete,
                                      pre_save)
from django.dispatch import receiver
from django.utils.timezone import now as utc_now

import caching.base
from django_statsd.clients import statsd
from south.signals import post_migrate

import remo.base.utils as utils
from remo.base.utils import (add_permissions_to_groups,
                             get_object_or_none, go_back_n_months)
from remo.base.models import GenericActiveManager
from remo.base.utils import daterange, get_date
from remo.events.helpers import get_event_link
from remo.events.models import Attendance as EventAttendance, Event
from remo.profiles.models import FunctionalArea
from remo.reports import (ACTIVITY_CAMPAIGN, ACTIVITY_EVENT_ATTEND,
                          ACTIVITY_EVENT_CREATE, READONLY_ACTIVITIES)
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
             'add_ngreport': ['Admin', 'Mentor'],
             'change_ngreport': ['Admin', 'Mentor'],
             'delete_ngreport': ['Admin', 'Mentor'],
             'delete_ngreportcomment': ['Admin', 'Mentor']}

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
class Activity(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    class Meta:
        ordering = ['name']
        verbose_name = 'activity'
        verbose_name_plural = 'activities'

    def __unicode__(self):
        return self.name

    def get_absolute_delete_url(self):
        return reverse('delete_activity', kwargs={'pk': self.id})

    def get_absolute_edit_url(self):
        return reverse('edit_activity', kwargs={'pk': self.id})

    @property
    def is_editable(self):
        """Check if activity is editable."""
        return not self.name in READONLY_ACTIVITIES


class Campaign(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    class Meta:
        ordering = ['name']
        verbose_name = 'campaign'
        verbose_name_plural = 'campaigns'

    def __unicode__(self):
        return self.name

    def get_absolute_delete_url(self):
        return reverse('delete_campaign', kwargs={'pk': self.id})

    def get_absolute_edit_url(self):
        return reverse('edit_campaign', kwargs={'pk': self.id})


class NGReport(caching.base.CachingMixin, models.Model):
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

    objects = caching.base.CachingManager()

    def _get_url_args(self):
        args = [self.user.userprofile.display_name,
                self.report_date.year,
                utils.number2month(self.report_date.month),
                self.report_date.day,
                self.id]
        return args

    def get_absolute_url(self):
        return reverse('remo.reports.views.view_ng_report',
                       args=self._get_url_args())

    def get_absolute_edit_url(self):
        return reverse('remo.reports.views.edit_ng_report',
                       args=self._get_url_args())

    def get_absolute_delete_url(self):
        return reverse('remo.reports.views.delete_ng_report',
                       args=self._get_url_args())

    @property
    def get_report_date(self):
        return self.report_date.strftime('%d %b %Y')

    @property
    def is_future_report(self):
        if self.report_date > utc_now().date():
            return True
        return False

    def save(self, *args, **kwargs):
        """Override save method."""
        one_week = datetime.timedelta(7)
        today = get_date()
        current_start = self.user.userprofile.current_streak_start or None
        longest_start = self.user.userprofile.longest_streak_start or None
        longest_end = self.user.userprofile.longest_streak_end or None

        # Save the mentor of the user if no mentor is defined.
        if not self.mentor:
            self.mentor = self.user.userprofile.mentor
        super(NGReport, self).save()

        if self.is_future_report:
            return

        # If there is already a running streak and the report date
        # is within this streak, update the current streak counter.
        if (current_start and self.report_date < current_start and
            self.report_date in daterange((current_start - one_week),
                                          current_start)):
            current_start = self.report_date
        # If there isn't any current streak, and the report date
        # is within the current week, let's start the counting.
        elif (not current_start and
                self.report_date in daterange(get_date(-7), today)):
            current_start = self.report_date

        # Longest streak section
        # If longest streak already exists, let's update it.
        if longest_start and longest_end:

            # Compare the number of reports registered during
            # the current streak and the number of reports
            # during the longest streak. If current streak is bigger
            # than the previous longest streak, update the longest streak.
            longest_streak_count = NGReport.objects.filter(
                report_date__range=(longest_start, longest_end),
                user=self.user).count()
            current_streak_count = NGReport.objects.filter(
                report_date__range=(current_start, today),
                user=self.user).count()
            if current_start and current_streak_count > longest_streak_count:
                longest_start = current_start
                longest_end = today

            # This happens only when a user appends a report, dated in the
            # range of longest streak counters and it's out of the range
            # of current streak counter.
            elif self.report_date in daterange(longest_start - one_week,
                                               longest_end + one_week):
                if self.report_date < longest_start:
                    longest_start = self.report_date
                elif self.report_date > longest_end:
                    longest_end = self.report_date
        else:
            # Longest streak counters are empty, let's setup their value
            longest_start = self.report_date
            longest_end = self.report_date
        # Assign the calculated values, to user's profile.
        self.user.userprofile.current_streak_start = current_start
        self.user.userprofile.longest_streak_start = longest_start
        self.user.userprofile.longest_streak_end = longest_end
        self.user.userprofile.save()

    class Meta:
        ordering = ['-report_date', '-created_on']

    def __unicode__(self):
        if self.activity.name == ACTIVITY_EVENT_ATTEND and self.event:
            return 'Attended event "%s"' % self.event.name
        elif self.activity.name == ACTIVITY_EVENT_CREATE and self.event:
            return 'Created event "%s"' % self.event.name
        elif self.activity.name == ACTIVITY_CAMPAIGN:
            return 'Participated in campaign "%s"' % self.campaign.name
        else:
            return self.activity.name


class NGReportComment(models.Model):
    """Comments in NGReport."""
    user = models.ForeignKey(User)
    report = models.ForeignKey(NGReport)
    created_on = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()

    def _get_url_args(self):
        args = [self.report.user.userprofile.display_name,
                self.report.report_date.year,
                utils.number2month(self.report.report_date.month),
                self.report.report_date.day,
                self.report.id,
                self.id]
        return args

    def get_absolute_delete_url(self):
        return reverse('remo.reports.views.delete_ng_report_comment',
                       args=self._get_url_args())

    class Meta:
        ordering = ['id']


@receiver(post_save, sender=EventAttendance,
          dispatch_uid='create_passive_attendance_report_signal')
def create_passive_attendance_report(sender, instance, **kwargs):
    """Automatically create a passive report after event attendance save."""
    if instance.user.groups.filter(name='Rep').exists():
        activity = Activity.objects.get(name=ACTIVITY_EVENT_ATTEND)
        attrs = {
            'user': instance.user,
            'event': instance.event,
            'activity': activity,
            'report_date': instance.event.start.date(),
            'longitude': instance.event.lon,
            'latitude': instance.event.lat,
            'location': "%s, %s, %s" % (instance.event.city,
                                        instance.event.region,
                                        instance.event.country),
            'is_passive': True,
            'link': get_event_link(instance.event),
            'activity_description': instance.event.description}

        report = NGReport.objects.create(**attrs)
        report.functional_areas.add(*instance.event.categories.all())
        statsd.incr('reports.create_passive_attendance')


@receiver(post_save, sender=Event,
          dispatch_uid='create_update_passive_event_creation_report_signal')
def create_update_passive_event_report(sender, instance, created, **kwargs):
    """Automatically create/update a passive report on event creation."""

    attrs = {
        'report_date': instance.start.date(),
        'longitude': instance.lon,
        'latitude': instance.lat,
        'location': "%s, %s, %s" % (instance.city,
                                    instance.region,
                                    instance.country),
        'link': get_event_link(instance),
        'activity_description': instance.description}

    if created:
        activity = Activity.objects.get(name=ACTIVITY_EVENT_CREATE)
        attrs.update({
            'user': instance.owner,
            'event': instance,
            'activity': activity,
            'is_passive': True})

        report = NGReport.objects.create(**attrs)
        report.functional_areas.add(*instance.categories.all())
        statsd.incr('reports.create_passive_event')
    else:
        NGReport.objects.filter(event=instance).update(**attrs)
        statsd.incr('reports.update_passive_event')


@receiver(pre_delete, sender=EventAttendance,
          dispatch_uid='delete_passive_report_attendance_signal')
def delete_passive_attendance_report(sender, instance, **kwargs):
    """Automatically delete a passive report after event attendance delete."""
    attrs = {
        'user': instance.user,
        'event': instance.event,
        'activity': Activity.objects.get(name=ACTIVITY_EVENT_ATTEND)}

    NGReport.objects.filter(**attrs).delete()
    statsd.incr('reports.delete_passive_attendance')


@receiver(pre_delete, sender=Event,
          dispatch_uid='delete_passive_report_event_signal')
def delete_passive_event_report(sender, instance, **kwargs):
    """Automatically delete a passive report after an event is deleted."""
    NGReport.objects.filter(event=instance).delete()
    statsd.incr('reports.delete_passive_event')


@receiver(pre_save, sender=Event,
          dispatch_uid='pre_update_passive_report_event_signal')
def update_passive_report_event_owner(sender, instance, **kwargs):
    """Automatically update passive reports event owner."""
    if instance.id:
        event = get_object_or_none(Event, pk=instance.id)
        if event and event.owner != instance.owner:
            attrs = {
                'user': event.owner,
                'event': instance,
                'activity': Activity.objects.get(name=ACTIVITY_EVENT_CREATE)}
            mentor = instance.owner.userprofile.mentor
            NGReport.objects.filter(**attrs).update(user=instance.owner,
                                                    mentor=mentor)


@receiver(m2m_changed, sender=Event.categories.through,
          dispatch_uid='update_passive_report_categories_signal')
def update_passive_report_functional_areas(sender, instance, action, pk_set,
                                           **kwargs):
    """Automatically update passive report's functional areas."""
    reports = NGReport.objects.filter(event=instance)

    for report in reports:
        if action == 'post_add':
            for pk in pk_set:
                obj = FunctionalArea.objects.get(id=pk)
                report.functional_areas.add(obj)

        if action == 'post_remove':
            for pk in pk_set:
                obj = FunctionalArea.objects.get(id=pk)
                report.functional_areas.remove(obj)

        if action == 'post_clear':
            report.functional_areas.clear()


@receiver(post_save, sender=NGReportComment,
          dispatch_uid='email_commenters_on_add_ng_report_comment_signal')
def email_commenters_on_add_ng_report_comment(sender, instance, **kwargs):
    """Email a user when a comment is added to a continuous report instance."""
    subject = '[Report] User {0} commented on {1}'
    email_template = 'emails/user_notification_on_add_ng_report_comment.txt'
    report = instance.report

    # Send an email to all users commented so far on the report except fom
    # the user who made the comment. Dedup the list with unique IDs.
    commenters = set(NGReportComment.objects.filter(report=report)
                     .exclude(user=instance.user)
                     .values_list('user', flat=True))

    # Add the owner of the report in the list
    if report.user.id not in commenters:
        commenters.add(report.user.id)

    for user_id in commenters:
        user = User.objects.get(pk=user_id)
        if (user.userprofile.receive_email_on_add_comment and
                user != instance.user):
            ctx_data = {'report': report, 'user': user,
                        'commenter': instance.user,
                        'comment': instance.comment,
                        'created_on': instance.created_on}
            subject = subject.format(instance.user.get_full_name(), report)
            send_remo_mail.delay([user_id], subject,
                                 email_template, ctx_data)
