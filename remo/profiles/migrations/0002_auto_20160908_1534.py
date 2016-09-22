# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Create 'Review' group."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.create(name='Review')


def backwards(apps, schema_editor):
    """Delete 'Review' group."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Review').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
