# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0003_auto_20160905_1315'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='poll',
            name='valid_groups',
        ),
    ]
