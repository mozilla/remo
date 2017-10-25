# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0005_groups_new_resources_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='MobilisingInterest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.SlugField(max_length=100, blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'mobilising skill',
                'verbose_name_plural': 'mobilising skills',
            },
        ),
        migrations.CreateModel(
            name='MobilisingSkill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.SlugField(max_length=100, blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'mobilising skill',
                'verbose_name_plural': 'mobilising skills',
            },
        ),
        migrations.AddField(
            model_name='userprofile',
            name='mobilising_interests',
            field=models.ManyToManyField(related_name='users_matching_interests', to='profiles.MobilisingInterest'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='mobilising_skills',
            field=models.ManyToManyField(related_name='users_matching_skills', to='profiles.MobilisingSkill'),
        ),
    ]
