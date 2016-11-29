# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import remo.profiles.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0003_auto_20160921_1608'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='rotm_nominated_by',
            field=models.ForeignKey(related_name='rotm_nominations', on_delete=django.db.models.deletion.SET_NULL, validators=[remo.profiles.models._validate_mentor], to=settings.AUTH_USER_MODEL, blank=True, null=True),
        ),
    ]
