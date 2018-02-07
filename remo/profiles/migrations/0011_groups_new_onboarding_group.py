# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Create Onboarding group."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.create(name='Onboarding')


def backwards(apps, schema_editor):
    """Delete Onboarding group."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Onboarding').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0010_auto_20171221_0112'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
