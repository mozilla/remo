# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'activity',
                'verbose_name_plural': 'activities',
            },
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'initiative',
                'verbose_name_plural': 'initiatives',
            },
        ),
        migrations.CreateModel(
            name='NGReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('report_date', models.DateField(db_index=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('longitude', models.FloatField(null=True)),
                ('latitude', models.FloatField(null=True)),
                ('location', models.CharField(default=b'', max_length=150, blank=True)),
                ('is_passive', models.BooleanField(default=False)),
                ('link', models.URLField(default=b'', max_length=500, blank=True)),
                ('link_description', models.CharField(default=b'', max_length=500, blank=True)),
                ('activity_description', models.TextField(default=b'', blank=True)),
                ('verified_activity', models.BooleanField(default=False, verbose_name=b'I have verified this activity')),
                ('country', models.CharField(default=b'', max_length=50, blank=True)),
                ('activity', models.ForeignKey(related_name='ng_reports', to='reports.Activity')),
                ('campaign', models.ForeignKey(related_name='ng_reports', blank=True, to='reports.Campaign', null=True)),
                ('event', models.ForeignKey(blank=True, to='events.Event', null=True)),
                ('functional_areas', models.ManyToManyField(related_name='ng_reports', to='profiles.FunctionalArea')),
                ('mentor', models.ForeignKey(related_name='ng_reports_mentored', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(related_name='ng_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-report_date', '-created_on'],
                'get_latest_by': 'report_date',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NGReportComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('comment', models.TextField()),
                ('report', models.ForeignKey(to='reports.NGReport')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
