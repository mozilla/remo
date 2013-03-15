from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.contrib.auth.models import Group, User
from django.db import models

from uuslug import uuslug as slugify


class Poll(models.Model):
    """Poll Abstract Model."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()
    valid_groups = models.ForeignKey(Group, related_name='valid_polls')
    created_on = models.DateField(auto_now_add=True)
    description = models.TextField(validators=[MaxLengthValidator(500),
                                               MinLengthValidator(20)])
    created_by = models.ForeignKey(User, related_name='polls_range_created')
    users_voted = models.ManyToManyField(User, related_name='polls_voted',
                                         through='Vote')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['-created_on']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.slug = slugify(self.name)
        super(Poll, self).save(*args, **kwargs)


class Vote(models.Model):
    """Vote model."""
    user = models.ForeignKey(User)
    ranged_poll = models.ForeignKey('Poll')
    date_voted = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return '%s %s' % (self.user, self.ranged_poll)


class PollRange(models.Model):
    """Poll Model for range voting."""
    name = models.CharField(max_length=500, default='')
    poll = models.ForeignKey('Poll')

    def __unicode__(self):
        return self.name


class PollRangeVotes(models.Model):
    """ Poll Range model to count votes."""
    votes = models.IntegerField(default=0)
    poll_range = models.ForeignKey('PollRange')
    nominee = models.ForeignKey(User)


class PollRadio(models.Model):
    """Poll Model for radio (Boolean) voting."""
    title = models.CharField(max_length=500)
    poll = models.ForeignKey('Poll')

    def __unicode__(self):
        return self.title


class PollChoices(models.Model):
    """Poll Model with available choices for radio voting."""
    answer = models.CharField(max_length=500)
    votes = models.IntegerField(default=0)
    radio_poll = models.ForeignKey('PollRadio')

    def __unicode__(self):
        return self.answer
