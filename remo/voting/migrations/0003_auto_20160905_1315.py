# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Migrate poll groups to m2m field."""
    Poll = apps.get_model('voting', 'Poll')
    polls = Poll.objects.all()
    for poll in polls:
        poll.poll_groups.add(poll.valid_groups)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0002_poll_poll_groups'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
