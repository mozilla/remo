# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Populate mozillian_username with username data."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.create(name='Review')


def backwards(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Review').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
