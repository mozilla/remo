# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc
import django.db.models.deletion
from django.conf import settings
import caching.base


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bug',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('bug_id', models.PositiveIntegerField(unique=True)),
                ('bug_creation_time', models.DateTimeField(null=True, blank=True)),
                ('bug_last_change_time', models.DateTimeField(null=True, blank=True)),
                ('component', models.CharField(max_length=200)),
                ('summary', models.CharField(default=b'', max_length=500)),
                ('whiteboard', models.CharField(default=b'', max_length=500)),
                ('status', models.CharField(default=b'', max_length=30)),
                ('resolution', models.CharField(default=b'', max_length=30)),
                ('first_comment', models.TextField(default=b'', blank=True)),
                ('council_vote_requested', models.BooleanField(default=False)),
                ('council_member_assigned', models.BooleanField(default=False)),
                ('pending_mentor_validation', models.BooleanField(default=False)),
                ('assigned_to', models.ForeignKey(related_name='bugs_assigned', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('budget_needinfo', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('cc', models.ManyToManyField(related_name='bugs_cced', to=settings.AUTH_USER_MODEL)),
                ('creator', models.ForeignKey(related_name='bugs_created', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-bug_last_change_time'],
            },
            bases=(caching.base.CachingMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_updated', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, tzinfo=utc))),
            ],
            options={
                'verbose_name_plural': 'statuses',
            },
        ),
    ]
