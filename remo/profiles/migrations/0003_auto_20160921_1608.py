# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Create Peers group."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.create(name='Peers')


def backwards(apps, schema_editor):
    """Delete Peers group."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Peers').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_auto_20160908_1534'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
