from pytz import timezone
from urlparse import urljoin

from django.conf import settings
from django.contrib.auth.models import Group, User, Permission
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from south.signals import post_migrate
from uuslug import uuslug as slugify

from remo.remozilla.models import Bug


class Attendance(models.Model):
    """Attendance Model."""
    user = models.ForeignKey(User)
    event = models.ForeignKey('Event')
    email = models.BooleanField(default=True)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (self.user, self.event)


class Event(models.Model):
    """Event Model."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()
    timezone = models.CharField(max_length=100)
    venue = models.CharField(max_length=50)
    city = models.CharField(max_length=50, blank=False, default='')
    region = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    lat = models.FloatField()
    lon = models.FloatField()
    external_link = models.URLField(max_length=300, null=True, blank=True)
    owner = models.ForeignKey(User, related_name='events_created')
    planning_pad_url = models.URLField(blank=True, max_length=300)
    estimated_attendance = models.PositiveIntegerField()
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

    def __unicode__(self):
        """Event unicode representation."""
        return self.name

    def _make_local(self, obj):
        """Return a datetime obj localized in self.timezone."""
        if not obj:
            return None
        t = timezone(self.timezone)
        return obj.astimezone(t)

    @property
    def local_start(self):
        """Property to start datetime localized."""
        return self._make_local(self.start)

    @property
    def local_end(self):
        """Property to end datetime localized."""
        return self._make_local(self.end)

    class Meta:
        ordering = ['start']
        permissions = (('can_subscribe_to_events', 'Can subscribe to events'),
                       ('can_edit_events', 'Can edit events'),
                       ('can_delete_events', 'Can delete events'))


class Metric(models.Model):
    """Metrics Model."""
    event = models.ForeignKey('Event', related_name='metrics')
    title = models.CharField(max_length=300)
    outcome = models.CharField(max_length=300)


@receiver(pre_save, sender=Event)
def create_slug(sender, instance, raw, **kwargs):
    """Auto create unique slug and calculate planning_pad_url."""
    if not instance.slug:
        instance.slug = slugify(instance.name, instance=instance)

    if not instance.planning_pad_url:
        url = urljoin(settings.ETHERPAD_URL,
                      getattr(settings, 'ETHERPAD_PREFIX', '') + instance.slug)
        instance.planning_pad_url = url


@receiver(post_save, sender=Event)
def subscribe_owner_to_event(sender, instance, raw, **kwargs):
    """Auto subscribe owner to Event."""
    if not raw:
        Attendance.objects.get_or_create(event=instance, user=instance.owner)


@receiver(post_migrate)
def event_set_groups(app, sender, signal, **kwargs):
    """Set permissions to groups."""
    if (isinstance(app, basestring) and app != 'events'):
        return True

    perms = {'can_edit_events': ['Admin', 'Council', 'Mentor', 'Rep'],
             'can_delete_events': ['Admin', 'Council', 'Mentor'],
             'can_subscribe_to_events': ['Admin', 'Council', 'Mentor', 'Rep']}

    for perm_name, groups in perms.iteritems():
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            permission = Permission.objects.get(codename=perm_name,
                                                content_type__name='event')
            group.permissions.add(permission)
