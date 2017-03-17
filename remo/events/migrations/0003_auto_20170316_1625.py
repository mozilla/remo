# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_auto_20160407_1156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventmetricoutcome',
            name='expected_outcome',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='eventmetricoutcome',
            name='outcome',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
    ]
