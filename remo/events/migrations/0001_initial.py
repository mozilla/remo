# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('remozilla', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.BooleanField(default=True)),
                ('date_subscribed', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=100, blank=True)),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('timezone', models.CharField(max_length=100)),
                ('venue', models.CharField(max_length=150)),
                ('city', models.CharField(default=b'', max_length=50)),
                ('region', models.CharField(default=b'', max_length=50, blank=True)),
                ('country', models.CharField(max_length=50)),
                ('lat', models.FloatField()),
                ('lon', models.FloatField()),
                ('external_link', models.URLField(max_length=300, null=True, blank=True)),
                ('planning_pad_url', models.URLField(max_length=300, blank=True)),
                ('estimated_attendance', models.PositiveIntegerField()),
                ('actual_attendance', models.PositiveIntegerField(null=True, blank=True)),
                ('description', models.TextField(validators=[django.core.validators.MaxLengthValidator(500), django.core.validators.MinLengthValidator(20)])),
                ('extra_content', models.TextField(default=b'', blank=True)),
                ('mozilla_event', models.BooleanField(default=False)),
                ('hashtag', models.CharField(default=b'', max_length=50, blank=True)),
                ('converted_visitors', models.PositiveIntegerField(default=0, editable=False)),
                ('times_edited', models.PositiveIntegerField(default=0, editable=False)),
                ('has_new_metrics', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_on', models.DateTimeField(auto_now=True, null=True)),
                ('attendees', models.ManyToManyField(related_name='events_attended', through='events.Attendance', to=settings.AUTH_USER_MODEL)),
                ('budget_bug', models.ForeignKey(related_name='event_budget_requests', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='remozilla.Bug', null=True)),
            ],
            options={
                'ordering': ['start'],
                'permissions': (('can_subscribe_to_events', 'Can subscribe to events'), ('can_edit_events', 'Can edit events'), ('can_delete_events', 'Can delete events'), ('can_delete_event_comments', 'Can delete event comments')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('comment', models.TextField()),
                ('event', models.ForeignKey(to='events.Event')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='EventGoal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=127, db_index=True)),
                ('slug', models.SlugField(max_length=127, blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'event goal',
                'verbose_name_plural': 'event goals',
            },
        ),
        migrations.CreateModel(
            name='EventMetric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='EventMetricOutcome',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('expected_outcome', models.IntegerField()),
                ('outcome', models.IntegerField(null=True, blank=True)),
                ('details', models.TextField(default=b'', blank=True, validators=[django.core.validators.MaxLengthValidator(1500)])),
                ('event', models.ForeignKey(to='events.Event')),
                ('metric', models.ForeignKey(to='events.EventMetric')),
            ],
            options={
                'verbose_name': 'event outcome',
                'verbose_name_plural': 'events outcome',
            },
        ),
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=300)),
                ('outcome', models.CharField(max_length=300)),
                ('event', models.ForeignKey(to='events.Event')),
            ],
        ),
    ]
