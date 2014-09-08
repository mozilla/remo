from pytz import timezone
from urlparse import urljoin

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

import caching.base
from south.signals import post_migrate
from uuslug import uuslug as slugify

from remo.base.models import GenericActiveManager
from remo.base.tasks import send_remo_mail
from remo.base.utils import add_permissions_to_groups
from remo.dashboard.models import ActionItem, Item
from remo.profiles.models import FunctionalArea
from remo.remozilla.models import Bug


SIMILAR_EVENTS = 3
SUBMIT_POST_EVENT_METRICS_ACTION = 'Submit post event metrics'


class Attendance(models.Model):
    """Attendance Model."""
    user = models.ForeignKey(User)
    event = models.ForeignKey('Event')
    email = models.BooleanField(default=True)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (self.user, self.event)


class EventGoal(models.Model):
    """Event Goals Model."""
    name = models.CharField(max_length=127, unique=True)
    slug = models.SlugField(blank=True, max_length=127)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    def save(self, *args, **kwargs):
        # Create unique slug
        if not self.slug:
            self.slug = slugify(self.name, instance=self)
        super(EventGoal, self).save(*args, **kwargs)

    def get_absolute_delete_url(self):
        return reverse('delete_event_goal', kwargs={'pk': self.id})

    def get_absolute_edit_url(self):
        return reverse('edit_event_goal', kwargs={'pk': self.id})

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'event goal'
        verbose_name_plural = 'event goals'


class EventMetric(models.Model):
    """New generation event metrics."""
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = GenericActiveManager()

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_delete_url(self):
        return reverse('delete_metric', kwargs={'pk': self.id})

    def get_absolute_edit_url(self):
        return reverse('edit_metric', kwargs={'pk': self.id})


class Event(caching.base.CachingMixin, models.Model):
    """Event Model."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()
    timezone = models.CharField(max_length=100)
    venue = models.CharField(max_length=150)
    city = models.CharField(max_length=50, blank=False, default='')
    region = models.CharField(max_length=50, null=False, blank=True,
                              default='')
    country = models.CharField(max_length=50)
    lat = models.FloatField()
    lon = models.FloatField()
    external_link = models.URLField(max_length=300, null=True, blank=True)
    owner = models.ForeignKey(User, related_name='events_created')
    planning_pad_url = models.URLField(blank=True, max_length=300)
    estimated_attendance = models.PositiveIntegerField()
    actual_attendance = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(validators=[MaxLengthValidator(500),
                                               MinLengthValidator(20)])
    extra_content = models.TextField(blank=True, default='')
    mozilla_event = models.BooleanField(default=False)
    hashtag = models.CharField(max_length=50, blank=True, default='')
    attendees = models.ManyToManyField(User, related_name='events_attended',
                                       through='Attendance')
    converted_visitors = models.PositiveIntegerField(editable=False, default=0)
    swag_bug = models.ForeignKey(Bug, null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='event_swag_requests')
    budget_bug = models.ForeignKey(Bug, null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   related_name='event_budget_requests')
    times_edited = models.PositiveIntegerField(default=0, editable=False)
    categories = models.ManyToManyField(FunctionalArea,
                                        related_name='events_categories')
    goals = models.ManyToManyField(EventGoal, related_name='events_goals')
    metrics = models.ManyToManyField(EventMetric, through='EventMetricOutcome')
    has_new_metrics = models.BooleanField(default=True)
    action_items = generic.GenericRelation(ActionItem)

    objects = caching.base.CachingManager()

    def get_absolute_edit_url(self):
        return reverse('events_edit_event', kwargs={'slug': self.slug})

    def __unicode__(self):
        """Event unicode representation."""
        return self.name

    def _make_local(self, obj):
        """Return a datetime obj localized in self.timezone."""
        if not obj:
            return None
        t = timezone(self.timezone)
        return obj.astimezone(t)

    def save(self, *args, **kwargs):
        """Override save method for custom functionality."""

        # Increment number of event edits
        self.times_edited += 1

        # Create unique slug
        if not self.slug:
            self.slug = slugify(self.name, instance=self)

        # Calculate planning pad url
        if not self.planning_pad_url:
            url = urljoin(settings.ETHERPAD_URL,
                          getattr(settings, 'ETHERPAD_PREFIX', '') + self.slug)
            self.planning_pad_url = url

        # Update action items
        if self.pk:
            current_event = Event.objects.get(id=self.pk)
            if current_event.owner != self.owner:
                model = ContentType.objects.get_for_model(self)
                action_items = ActionItem.objects.filter(content_type=model,
                                                         object_id=self.pk)
                action_items.update(user=self.owner)

        super(Event, self).save(*args, **kwargs)

        # Subscribe owner to event
        Attendance.objects.get_or_create(event=self, user=self.owner)

    @property
    def local_start(self):
        """Property to start datetime localized."""
        return self._make_local(self.start)

    @property
    def local_end(self):
        """Property to end datetime localized."""
        return self._make_local(self.end)

    @property
    def is_past_event(self):
        """Property to check is event is in the past."""
        if self.id:
            return now() > self.end
        return None

    def get_similar_events(self):
        """Implement 3-events-like-this functionality.

        Specs:

        * Return future events that match the same country and one or
          more categories.
        * If less than 3 matches, show upcoming events with the same country.
        * If less than 3 matches, show upcoming events with the same category.
        * Order by date, earliest date first.

        """

        events = Event.objects.filter(start__gte=now()).exclude(pk=self.pk)
        country = Q(country=self.country)
        category = Q(categories__in=self.categories.all())

        if ((events.filter(country, category).distinct().count() <
             SIMILAR_EVENTS)):
            if events.filter(country).count() < SIMILAR_EVENTS:
                return events.filter(category).distinct()
            return events.filter(country)
        return events.filter(country, category).distinct()

    def get_action_items(self):
        action_items = []

        # Get action items for post event metrics
        outcome = self.eventmetricoutcome_set.filter(outcome__isnull=False)
        if self.is_past_event and not outcome and self.has_new_metrics:
            action_item = Item(SUBMIT_POST_EVENT_METRICS_ACTION, self.owner,
                               ActionItem.NORMAL, None)
            action_items.append(action_item)
        return action_items

    class Meta:
        ordering = ['start']
        permissions = (('can_subscribe_to_events', 'Can subscribe to events'),
                       ('can_edit_events', 'Can edit events'),
                       ('can_delete_events', 'Can delete events'),
                       ('can_delete_event_comments',
                        'Can delete event comments'))


class EventMetricOutcome(models.Model):
    """New generation event metric stats."""
    event = models.ForeignKey(Event)
    metric = models.ForeignKey(EventMetric)
    expected_outcome = models.IntegerField()
    outcome = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'event outcome'
        verbose_name_plural = 'events outcome'

    def save(self, *args, **kwargs):
        super(EventMetricOutcome, self).save(*args, **kwargs)

        # Resolve action items for post event metrics
        ActionItem.resolve(instance=self.event,
                           user=self.event.owner,
                           name='Submit post event metrics')


class EventComment(models.Model):
    """Comments in Event."""
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    created_on = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()

    class Meta:
        ordering = ['id']


class Metric(models.Model):
    """Metrics Model."""
    event = models.ForeignKey('Event')
    title = models.CharField(max_length=300)
    outcome = models.CharField(max_length=300)


@receiver(post_migrate, dispatch_uid='event_set_groups_signal')
def event_set_groups(app, sender, signal, **kwargs):
    """Set permissions to groups."""
    if (isinstance(app, basestring) and app != 'events'):
        return True

    perms = {'can_edit_events': ['Admin', 'Council', 'Mentor', 'Rep'],
             'can_delete_events': ['Admin', 'Council', 'Mentor'],
             'can_delete_event_comments': ['Admin'],
             'can_subscribe_to_events': ['Admin', 'Council', 'Mentor', 'Rep',
                                         'Mozillians']}

    add_permissions_to_groups('events', perms)


@receiver(post_save, sender=EventComment,
          dispatch_uid='email_event_owner_on_add_comment_signal')
def email_event_owner_on_add_comment(sender, instance, **kwargs):
    """Email event owner when a comment is added to event."""
    subject = '[Event] User %s commented on event "%s"'
    email_template = 'email/owner_notification_on_add_comment.txt'
    event = instance.event
    owner = instance.event.owner
    event_url = reverse('events_view_event', kwargs={'slug': event.slug})
    ctx_data = {'event': event, 'owner': owner, 'user': instance.user,
                'comment': instance.comment, 'event_url': event_url}
    if owner.userprofile.receive_email_on_add_event_comment:
        subject = subject % (instance.user.get_full_name(),
                             instance.event.name)
        send_remo_mail.delay(subject=subject, recipients_list=[owner.id],
                             email_template=email_template, data=ctx_data)
