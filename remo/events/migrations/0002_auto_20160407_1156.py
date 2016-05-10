# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
        ('events', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0001_initial'),
        ('remozilla', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='campaign',
            field=models.ForeignKey(related_name='events', to='reports.Campaign', null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='categories',
            field=models.ManyToManyField(related_name='events_categories', to='profiles.FunctionalArea', blank=True),
        ),
        migrations.AddField(
            model_name='event',
            name='goals',
            field=models.ManyToManyField(related_name='events_goals', to='events.EventGoal', blank=True),
        ),
        migrations.AddField(
            model_name='event',
            name='metrics',
            field=models.ManyToManyField(to='events.EventMetric', through='events.EventMetricOutcome'),
        ),
        migrations.AddField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(related_name='events_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='swag_bug',
            field=models.ForeignKey(related_name='event_swag_requests', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='remozilla.Bug', null=True),
        ),
        migrations.AddField(
            model_name='attendance',
            name='event',
            field=models.ForeignKey(to='events.Event'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
