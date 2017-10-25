# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0007_auto_20171025_1000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='mobilising_interests',
            field=models.ManyToManyField(related_name='users_matching_interests', to='profiles.MobilisingInterest', blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='mobilising_skills',
            field=models.ManyToManyField(related_name='users_matching_skills', to='profiles.MobilisingSkill', blank=True),
        ),
    ]
