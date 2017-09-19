import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now

import caching.base
from product_details import product_details

import remo.base.utils as utils
from remo.base.models import GenericActiveManager
from remo.base.utils import daterange, get_date, get_object_or_none
from remo.dashboard.models import ActionItem, Item
from remo.events.models import Event
from remo.profiles.models import FunctionalArea
from remo.reports import (ACTIVITY_CAMPAIGN, ACTIVITY_EVENT_ATTEND,
                          ACTIVITY_EVENT_CREATE, READONLY_ACTIVITIES, VERIFIABLE_ACTIVITIES)


COUNTRIES_LIST = product_details.get_regions('en').values()
VERIFY_ACTIVITY_WEEKS = 2
VERIFY_ACTION = 'Verify the activity of'


@python_2_unicode_compatible
class Activity(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    class Meta:
        ordering = ['name']
        verbose_name = 'activity'
        verbose_name_plural = 'activities'

    def __str__(self):
        return self.name

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


@python_2_unicode_compatible
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

    def __str__(self):
        return self.name

    def get_absolute_edit_url(self):
        return reverse('edit_campaign', kwargs={'pk': self.id})


@python_2_unicode_compatible
class NGReport(caching.base.CachingMixin, models.Model):
    """ Continuous Reporting Model.

    In order to be able to distinguish the old
    and the new Report models, each model associated
    with the continuous reporting system will have the
    'NG' prefix (NG - New Generation).
    """
    user = models.ForeignKey(User, related_name='ng_reports')
    report_date = models.DateField(db_index=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    mentor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL,
                               related_name='ng_reports_mentored')
    activity = models.ForeignKey(Activity, related_name='ng_reports')
    campaign = models.ForeignKey(Campaign, null=True, blank=True, related_name='ng_reports')
    functional_areas = models.ManyToManyField(FunctionalArea, related_name='ng_reports')
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
    action_items = GenericRelation(ActionItem)

    objects = caching.base.CachingManager()

    def _get_url_args(self):
        args = [self.user.userprofile.display_name,
                self.report_date.year,
                utils.number2month(self.report_date.month),
                self.report_date.day,
                self.id]
        return args

    def get_absolute_url(self):
        return reverse('remo.reports.views.view_ng_report', args=self._get_url_args())

    def get_absolute_edit_url(self):
        return reverse('remo.reports.views.edit_ng_report', args=self._get_url_args())

    def get_absolute_delete_url(self):
        return reverse('remo.reports.views.delete_ng_report', args=self._get_url_args())

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

        # Resolve the verified action items.
        action_item_name = u'{0} {1}'.format(VERIFY_ACTION, self.user.get_full_name())
        if self.verified_activity:
            ActionItem.resolve(instance=self,
                               user=self.mentor,
                               name=action_item_name)
        else:
            # Create all the action items, if any
            ActionItem.create(self)

        if self.is_future_report:
            return

        # If there is already a running streak and the report date
        # is within this streak, update the current streak counter.
        if (current_start and self.report_date < current_start and
                self.report_date in daterange((current_start - one_week), current_start)):
            current_start = self.report_date
        # If there isn't any current streak, and the report date
        # is within the current week, let's start the counting.
        elif not current_start and self.report_date in daterange(get_date(-7), today):
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
            elif self.report_date in daterange(longest_start - one_week, longest_end + one_week):
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

    def get_action_items(self):
        """Returns a list of action items.

        An action item is returned in the case that an activity needs
        verification from the mentor of a user.
        """

        action_items = []
        if self.activity.is_verifiable and not self.verified_activity:
            due_date = get_date(weeks=VERIFY_ACTIVITY_WEEKS)
            name = u'{0} {1}'.format(VERIFY_ACTION, self.user.get_full_name())
            priority = ActionItem.NORMAL
            action_items.append(Item(name, self.mentor, priority, due_date))
        return action_items

    class Meta:
        ordering = ['-report_date', '-created_on']
        get_latest_by = 'report_date'

    def __str__(self):
        if self.activity.name == ACTIVITY_EVENT_ATTEND and self.event:
            return u'Attended event "%s"' % self.event.name
        elif self.activity.name == ACTIVITY_EVENT_CREATE and self.event:
            return u'Organized event "%s"' % self.event.name
        elif self.activity.name == ACTIVITY_CAMPAIGN:
            return u'Participated in campaign "%s"' % self.campaign.name
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
