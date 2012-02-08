from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class FeaturedRep(models.Model):
    user = models.ForeignKey(User)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name="reps_featured")
    text = models.TextField(blank=False, null=False)

    class Meta:
        ordering = ('-updated_on',)
        get_latest_by = 'updated_on'
