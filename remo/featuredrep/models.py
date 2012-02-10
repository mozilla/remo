from django.db import models
from django.contrib.auth.models import User
# alphabetize imports

# Create your models here. <-- remove comment, not needed.
class FeaturedRep(models.Model):
    # Missing comment for class
    user = models.ForeignKey(User)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name="reps_featured")
    text = models.TextField(blank=False, null=False)

    class Meta:
        ordering = ('-updated_on',)
        get_latest_by = 'updated_on'
