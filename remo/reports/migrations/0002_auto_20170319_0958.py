# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def create_activities(apps, schema_editor):
    """Create the activiteis listed in reports/__init__.py
    if they don't exist.
    """
    from remo.reports import READONLY_ACTIVITIES, UNLISTED_ACTIVITIES
    Activity = apps.get_model('reports', 'Activity')
    all_activities = READONLY_ACTIVITIES
    all_activities.extend(x for x in UNLISTED_ACTIVITIES if x not in all_activities)

    for activity in all_activities:
        if not Activity.objects.filter(name=activity).exists():
            Activity.objects.create(name=activity)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_activities, backwards)
    ]
