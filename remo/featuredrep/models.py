from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.utils.timezone import now

from south.signals import post_migrate

from remo.base.utils import add_permissions_to_groups


class FeaturedRep(models.Model):
    """Featured Rep model.

    Featured Rep -or Rep of the Month- relates existing users with
    some text explaining why they are so cool.

    """
    created_on = models.DateTimeField(null=True, blank=True)
    updated_on = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='reps_featured')
    text = models.TextField(blank=False, null=False)
    users = models.ManyToManyField(User, related_name='featuredrep_users')

    class Meta:
        ordering = ['-updated_on']
        get_latest_by = 'updated_on'
        permissions = (('can_edit_featured', 'Can edit featured reps'),
                       ('can_delete_featured', 'Can delete featured reps'))

    def save(self, *args, **kwargs):
        """Override save method for custom functionality"""

        # This allows to override the updated_on through the admin interface
        self.updated_on = kwargs.pop('updated_on', None)

        if not self.updated_on:
            self.updated_on = now()
        if not self.pk:
            self.created_on = now()
        super(FeaturedRep, self).save(*args, **kwargs)


@receiver(post_migrate, dispatch_uid='featuredrep_set_groups_signal')
def featuredrep_set_groups(app, sender, signal, **kwargs):
    """Set permissions to groups."""
    if (isinstance(app, basestring) and app != 'featuredrep'):
        return True

    perms = {'can_edit_featured': ['Admin', 'Council'],
             'can_delete_featured': ['Admin', 'Council']}

    add_permissions_to_groups('featuredrep', perms)
