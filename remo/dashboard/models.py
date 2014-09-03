from django.db import models
from django.contrib.auth.models import User

from uuslug import uuslug


class ActionItem(models.Model):
    """ActionItem Model."""

    # List of priorities - borrowed from bugzilla
    MINOR = 1
    NORMAL = 2
    MAJOR = 3
    CRITICAL = 4
    BLOCKER = 5
    PRIORITY_CHOICES = (
        (MINOR, 'Minor'),
        (NORMAL, 'Normal'),
        (MAJOR, 'Major'),
        (CRITICAL, 'Critical'),
        (BLOCKER, 'Blocker'),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(blank=True, max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    due_date = models.DateField()
    priority = models.IntegerField(choices=PRIORITY_CHOICES)
    user = models.ForeignKey(User, related_name='action_items_assigned')

    class Meta:
        ordering = ['-due_date', '-updated_on', '-created_on']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Override save method for custom functionality."""
        if not self.pk:
            self.slug = uuslug(self.name, instance=self)

        super(ActionItem, self).save(*args, **kwargs)
