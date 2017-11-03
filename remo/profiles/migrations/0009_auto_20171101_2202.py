# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0008_auto_20171025_2031'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mobilisinginterest',
            options={'ordering': ['name'], 'verbose_name': 'mobilizing learning interest', 'verbose_name_plural': 'mobilizing learning interests'},
        ),
        migrations.AlterModelOptions(
            name='mobilisingskill',
            options={'ordering': ['name'], 'verbose_name': 'mobilizing expertise', 'verbose_name_plural': 'mobilizing expertise'},
        ),
    ]
