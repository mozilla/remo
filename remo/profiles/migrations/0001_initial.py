# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import remo.base.utils
import remo.profiles.models
import django.db.models.deletion
from django.conf import settings
import caching.base
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FunctionalArea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.SlugField(max_length=100, blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'functional area',
                'verbose_name_plural': 'functional areas',
            },
        ),
        migrations.CreateModel(
            name='UserAvatar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('avatar_url', models.URLField(default=b'', max_length=400)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            bases=(caching.base.CachingMixin, models.Model),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('registration_complete', models.BooleanField(default=False)),
                ('date_joined_program', models.DateField(blank=True)),
                ('date_left_program', models.DateField(null=True, blank=True)),
                ('local_name', models.CharField(default=b'', max_length=100, blank=True)),
                ('birth_date', models.DateField(blank=True, null=True, validators=[remo.profiles.models._validate_birth_date])),
                ('city', models.CharField(default=b'', max_length=50)),
                ('region', models.CharField(default=b'', max_length=50)),
                ('country', models.CharField(default=b'', max_length=50)),
                ('lon', models.FloatField(null=True)),
                ('lat', models.FloatField(null=True)),
                ('display_name', models.CharField(default=b'', unique=True, max_length=50, blank=True, validators=[django.core.validators.RegexValidator(regex=b'("")|(^[A-Za-z0-9_]+$)', message=b'Please only A-Z characters, numbers and underscores.')])),
                ('private_email', models.EmailField(default=b'', max_length=254, null=True)),
                ('mozillians_profile_url', models.URLField(validators=[django.core.validators.RegexValidator(regex=b'^http(s)?://(www\\.)?mozillians.org/', message=b'Please provide a valid Mozillians url.')])),
                ('twitter_account', models.CharField(default=b'', max_length=16, blank=True, validators=[django.core.validators.RegexValidator(regex=b'("^$")|(^[A-Za-z0-9_]+$)', message=b'Please provide a valid Twitter handle.')])),
                ('jabber_id', models.CharField(default=b'', max_length=50, blank=True)),
                ('irc_name', models.CharField(default=b'', max_length=50)),
                ('irc_channels', models.TextField(default=b'', blank=True)),
                ('linkedin_url', models.URLField(default=b'', blank=True, validators=[django.core.validators.RegexValidator(regex=b'("^$")|(^http(s)?://(.*?)linkedin.com/)', message=b'Please provide a valid LinkedIn url.')])),
                ('facebook_url', models.URLField(default=b'', blank=True, validators=[django.core.validators.RegexValidator(regex=b'("^$")|(^http(s)?://(.*?)facebook.com/)', message=b'Please provide a valid Facebook url.')])),
                ('diaspora_url', models.URLField(default=b'', blank=True)),
                ('personal_website_url', models.URLField(default=b'', blank=True)),
                ('personal_blog_feed', models.URLField(default=b'', blank=True)),
                ('wiki_profile_url', models.URLField(default=b'', blank=True, validators=[django.core.validators.RegexValidator(regex=b'^http(s)?://wiki.mozilla.org/User:', message=b'Please provide a valid wiki url.')])),
                ('bio', models.TextField(default=b'', blank=True)),
                ('gender', models.NullBooleanField(default=None, choices=[(None, b'Gender'), (True, b'Female'), (False, b'Male')])),
                ('receive_email_on_add_comment', models.BooleanField(default=True)),
                ('receive_email_on_add_event_comment', models.BooleanField(default=True)),
                ('receive_email_on_add_voting_comment', models.BooleanField(default=True)),
                ('mozillian_username', models.CharField(default=b'', max_length=40, blank=True)),
                ('current_streak_start', models.DateField(null=True, blank=True)),
                ('longest_streak_start', models.DateField(null=True, blank=True)),
                ('longest_streak_end', models.DateField(null=True, blank=True)),
                ('first_report_notification', models.DateField(null=True, blank=True)),
                ('second_report_notification', models.DateField(null=True, blank=True)),
                ('timezone', models.CharField(default=b'', max_length=100, blank=True)),
                ('unavailability_task_id', models.CharField(default=b'', max_length=256, null=True, editable=False, blank=True)),
                ('is_rotm_nominee', models.BooleanField(default=False)),
                ('added_by', models.ForeignKey(related_name='users_added', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('functional_areas', models.ManyToManyField(related_name='users_matching', to='profiles.FunctionalArea')),
                ('mentor', models.ForeignKey(related_name='mentees', on_delete=django.db.models.deletion.SET_NULL, validators=[remo.profiles.models._validate_mentor], to=settings.AUTH_USER_MODEL, blank=True, null=True)),
                ('tracked_functional_areas', models.ManyToManyField(related_name='users_tracking', to='profiles.FunctionalArea')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': (('create_user', 'Can create new user'), ('can_edit_profiles', 'Can edit profiles'), ('can_delete_profiles', 'Can delete profiles')),
            },
            bases=(caching.base.CachingMixin, models.Model),
        ),
        migrations.CreateModel(
            name='UserStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField(default=remo.base.utils.get_date, blank=True)),
                ('expected_date', models.DateField(null=True, blank=True)),
                ('return_date', models.DateField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('is_unavailable', models.BooleanField(default=False)),
                ('replacement_rep', models.ForeignKey(related_name='replaced_rep', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(related_name='status', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-expected_date', '-created_on'],
                'verbose_name_plural': 'User Statuses',
            },
            bases=(caching.base.CachingMixin, models.Model),
        ),
    ]
