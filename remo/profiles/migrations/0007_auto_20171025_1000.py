# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_auto_20171025_0807'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mobilisinginterest',
            options={'ordering': ['name'], 'verbose_name': 'mobilising interest', 'verbose_name_plural': 'mobilising interests'},
        ),
    ]
