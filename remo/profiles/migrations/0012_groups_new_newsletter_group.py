# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Create Newsletter group."""
    Group = apps.get_model('auth', 'Group')
    if not Group.objects.filter(name='Newsletter').exists():
        Group.objects.create(name='Newsletter')


def backwards(apps, schema_editor):
    """Delete Newsletter group."""
    Group = apps.get_model('auth', 'Group')
    if Group.objects.filter(name='Newsletter').exists():
        Group.objects.filter(name='Newsletter').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0011_groups_new_onboarding_group'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
