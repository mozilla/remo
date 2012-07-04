from urlparse import urljoin

from django.conf import settings
from django.contrib.auth.models import Group, User, Permission
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from south.signals import post_migrate
from uuslug import uuslug as slugify

EST_ATTENDANCE_CHOICES = ((10, '<10'),
                          (50, '10-50'),
                          (100, '50-100'),
                          (500, '100-500'),
                          (1000, '500-1000'),
                          (2000, '>1000'))


class Attendance(models.Model):
    """Attendance Model."""
    user = models.ForeignKey(User)
    event = models.ForeignKey('Event')
    email = models.BooleanField(default=True)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (self.user, self.event)


class Metric(models.Model):
    """Metrics Model."""
    event = models.ForeignKey('Event', related_name='metrics')
    title = models.CharField(max_length=300)
    outcome = models.CharField(max_length=300)


class Event(models.Model):
    """Event Model."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()
    venue = models.CharField(max_length=50)
    region = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    external_link = models.URLField(max_length=300, null=True, blank=True)
    owner = models.ForeignKey(User, related_name='events_created')
    planning_pad_url = models.URLField(max_length=300)
    estimated_attendance = models.PositiveIntegerField(
        choices=EST_ATTENDANCE_CHOICES)
    description = models.TextField()
    extra_content = models.TextField(blank=True, default='')
    mozilla_event = models.BooleanField(default=False)
    virtual_event = models.BooleanField(default=False)
    hashtag = models.CharField(max_length=50, null=True, default='')
    attendees = models.ManyToManyField(User, related_name='events_attended',
                                       through='Attendance')
    converted_visitors = models.PositiveIntegerField(editable=False,
                                                     default=0)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['-start']
        permissions = (('can_subscribe_to_events', 'Can subscribe to events'),
                       ('can_edit_events', 'Can edit events'),
                       ('can_delete_events', 'Can delete events'))


@receiver(pre_save, sender=Event)
def create_slug(sender, instance, raw, **kwargs):
    """Auto create unique slug for Event."""
    if not instance.slug:
        instance.slug = slugify(instance.name, instance=instance)


@receiver(pre_save, sender=Event)
def create_planning_pad_url(sender, instance, raw, **kwargs):
    """Auto planning pad url for Event."""
    if not instance.planning_pad_url:
        instance.planning_pad_url = urljoin(settings.ETHERPAD_URL,
                                            instance.slug)


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
