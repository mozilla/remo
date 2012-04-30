from django.contrib.auth.models import User
from django.db import models

from remo.base.models import UTCDateTimeField

class FeaturedRep(models.Model):
    """Featured Rep model.

    Featured Rep -or Rep of the Month- relates existing users with
    some text explaining why they are so cool.

    """
    user = models.ForeignKey(User)
    created_on = UTCDateTimeField(auto_now_add=True)
    updated_on = UTCDateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='reps_featured')
    text = models.TextField(blank=False, null=False)

    class Meta:
        ordering = ['-updated_on']
        get_latest_by = 'updated_on'
