# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Create Resources group."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.create(name='Resources')


def backwards(apps, schema_editor):
    """Delete Resources group."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Resources').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_userprofile_rotm_nominated_by'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
