import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver
from django.utils.timezone import now

import caching.base
from django_statsd.clients import statsd
from product_details import product_details
from south.signals import post_migrate

import remo.base.utils as utils
from remo.base.utils import add_permissions_to_groups
from remo.base.models import GenericActiveManager
from remo.base.tasks import send_remo_mail
from remo.base.utils import daterange, get_date
from remo.events.models import Attendance as EventAttendance, Event
from remo.profiles.models import FunctionalArea
from remo.reports import (ACTIVITY_CAMPAIGN, ACTIVITY_EVENT_ATTEND,
                          ACTIVITY_EVENT_CREATE, ACTIVITY_POST_EVENT_METRICS,
                          READONLY_ACTIVITIES, VERIFIABLE_ACTIVITIES)
COUNTRIES_LIST = product_details.get_regions('en').values()


@receiver(post_migrate, dispatch_uid='report_set_groups_signal')
def report_set_groups(app, sender, signal, **kwargs):
    """Set permissions to groups."""
    if (isinstance(app, basestring) and app != 'reports'):
        return True

    perms = {'add_ngreport': ['Admin', 'Mentor'],
             'change_ngreport': ['Admin', 'Mentor'],
             'delete_ngreport': ['Admin', 'Mentor'],
             'delete_ngreportcomment': ['Admin', 'Mentor']}

    add_permissions_to_groups('reports', perms)


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
        return self.name not in READONLY_ACTIVITIES

    @property
    def is_verifiable(self):
        """Check if the activity is verifiable."""
        if self.name in VERIFIABLE_ACTIVITIES:
            return True
        return False


class Campaign(models.Model):
    """Campaign/Initiatives model.

    As of March 2015 this serves as the Initiative model used both
    in events and reports app.
    """
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    class Meta:
        ordering = ['name']
        verbose_name = 'initiative'
        verbose_name_plural = 'initiatives'

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
    link_description = models.CharField(max_length=500, blank=True, default='')
    activity_description = models.TextField(blank=True, default='')
    verified_activity = models.BooleanField('I have verified this activity',
                                            blank=True, default=False)
    country = models.CharField(max_length=50, blank=True, default='')

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
        if self.report_date > now().date():
            return True
        return False

    def save(self, *args, **kwargs):
        """Override save for custom functionality."""

        # Make last report notificaton date NULL on new report
        today = get_date()
        if self.pk is None and self.user.userprofile.first_report_notification:
            start = today - datetime.timedelta(weeks=4)
            end = today + datetime.timedelta(weeks=4)
            if self.report_date in daterange(start, end):
                self.user.userprofile.first_report_notification = None
                self.user.userprofile.second_report_notification = None
                self.user.userprofile.save()

        # User streaks functionality
        one_week = datetime.timedelta(7)
        current_start = self.user.userprofile.current_streak_start or None
        longest_start = self.user.userprofile.longest_streak_start or None
        longest_end = self.user.userprofile.longest_streak_end or None

        # Save the mentor of the user if no mentor is defined.
        if not self.mentor:
            self.mentor = self.user.userprofile.mentor
        # Save the country if possible
        saved_report = get_object_or_none(NGReport, id=self.id)
        if (saved_report and (saved_report.latitude != self.latitude or
                              saved_report.longitude != self.longitude)):
            country = None
            try:
                country = self.location.split(',')[-1].strip()
            except IndexError:
                pass
            if country in COUNTRIES_LIST:
                self.country = country
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
        get_latest_by = 'report_date'

    def __unicode__(self):
        if self.activity.name == ACTIVITY_EVENT_ATTEND and self.event:
            return 'Attended event "%s"' % self.event.name
        elif self.activity.name == ACTIVITY_EVENT_CREATE and self.event:
            return 'Organized event "%s"' % self.event.name
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
    from remo.events.helpers import get_event_link

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
            'country': instance.event.country,
            'link': get_event_link(instance.event),
            'activity_description': instance.event.description}

        report = NGReport.objects.create(**attrs)
        report.functional_areas.add(*instance.event.categories.all())
        statsd.incr('reports.create_passive_attendance')


@receiver(post_save, sender=Event,
          dispatch_uid='create_update_passive_event_creation_report_signal')
def create_update_passive_event_report(sender, instance, created, **kwargs):
    """Automatically create/update a passive report on event creation."""
    from remo.events.helpers import get_event_link

    attrs = {
        'report_date': instance.start.date(),
        'longitude': instance.lon,
        'latitude': instance.lat,
        'location': "%s, %s, %s" % (instance.city,
                                    instance.region,
                                    instance.country),
        'link': get_event_link(instance),
        'activity_description': instance.description,
        'is_passive': True,
        'event': instance,
        'campaign': instance.campaign,
        'country': instance.country
    }

    if created:
        activity = Activity.objects.get(name=ACTIVITY_EVENT_CREATE)
        attrs.update({'user': instance.owner,
                      'activity': activity})

        NGReport.objects.create(**attrs)
        statsd.incr('reports.create_passive_event')
    else:
        reports = (NGReport.objects.filter(event=instance)
                   .exclude(activity__name=ACTIVITY_POST_EVENT_METRICS))
        reports.update(**attrs)
        # Change user and mentor to the appropriate reports
        attrs.update({'user': instance.owner,
                      'mentor': instance.owner.userprofile.mentor})
        reports.exclude(activity__name=ACTIVITY_EVENT_ATTEND).update(**attrs)
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
            send_remo_mail.delay(subject=subject, recipients_list=[user_id],
                                 email_template=email_template, data=ctx_data)


@receiver(pre_delete, sender=NGReport,
          dispatch_uid='delete_ng_report_signal')
def delete_ng_report(sender, instance, **kwargs):
    """Automatically update user's streak counters."""
    today = get_date()
    current_start = instance.user.userprofile.current_streak_start or None
    longest_start = instance.user.userprofile.longest_streak_start or None
    longest_end = instance.user.userprofile.longest_streak_end or None

    # If instance is in the future or there is another
    # report that date, don't do anything
    if (instance.is_future_report or
        (NGReport.objects
         .filter(user=instance.user, report_date=instance.report_date)
         .exclude(pk=instance.id).exists())):
        return

    try:
        next_report = instance.get_next_by_report_date(
            user=instance.user, report_date__lte=today)
    except NGReport.DoesNotExist:
        next_report = None

    try:
        previous_report = instance.get_previous_by_report_date(
            user=instance.user)
    except NGReport.DoesNotExist:
        previous_report = None

    # There aren't any reports
    if not next_report and not previous_report:
        current_start = None
        longest_start = None
        longest_end = None

    # If the deleted report is between the range of the longest
    # streak counters, we need to update them.
    elif (longest_start and longest_end and
          instance.report_date in daterange(longest_start, longest_end)):

        if longest_start == instance.report_date and next_report:
            longest_start = next_report.report_date
        elif longest_end == instance.report_date and previous_report:
            longest_end = previous_report.report_date
        elif (previous_report and next_report and
              (next_report.report_date -
               previous_report.report_date).days > 7):
            # Compare the number of reports registered from the starting point
            # of the longest streak up until the date of the deleted report,
            # with the number of reports registered from the date of the
            # deleted report until the end of the longest streak.
            lower_half_report_count = NGReport.objects.filter(
                report_date__range=(longest_start, instance.report_date),
                user=instance.user).count()
            upper_half_report_count = NGReport.objects.filter(
                report_date__range=(instance.report_date, longest_end),
                user=instance.user).count()

            # If the first time slice contains more reports, then we need
            # to move the end of the longest streak, just before
            # the deletion point. If the opposite is true, move the starting
            # point of the longest streak just after the deletion point.
            if (lower_half_report_count >= upper_half_report_count and
                    previous_report.report_date >= longest_start):
                longest_end = previous_report.report_date
            elif (upper_half_report_count > lower_half_report_count and
                    next_report.report_date <= longest_end):
                longest_start = next_report.report_date

    # If the deleted report is between the range of the current
    # streak counter and today, then we need to update the counter.
    if (current_start and
            instance.report_date in daterange(current_start, today)):
        if current_start == instance.report_date and next_report:
            current_start = next_report.report_date
        elif (previous_report and next_report and
                (next_report.report_date -
                 previous_report.report_date).days > 7):
            current_start = next_report.report_date

    instance.user.userprofile.current_streak_start = current_start
    instance.user.userprofile.longest_streak_start = longest_start
    instance.user.userprofile.longest_streak_end = longest_end
    instance.user.userprofile.save()
