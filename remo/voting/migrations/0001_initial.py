# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
        ('remozilla', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=300)),
                ('slug', models.SlugField(max_length=255, blank=True)),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(validators=[django.core.validators.MaxLengthValidator(2500), django.core.validators.MinLengthValidator(20)])),
                ('task_start_id', models.CharField(default=b'', max_length=256, null=True, editable=False, blank=True)),
                ('task_end_id', models.CharField(default=b'', max_length=256, null=True, editable=False, blank=True)),
                ('automated_poll', models.BooleanField(default=False)),
                ('comments_allowed', models.BooleanField(default=True)),
                ('is_extended', models.BooleanField(default=False)),
                ('bug', models.ForeignKey(blank=True, to='remozilla.Bug', null=True)),
                ('created_by', models.ForeignKey(related_name='range_polls_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_on'],
            },
        ),
        migrations.CreateModel(
            name='PollComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('comment', models.TextField()),
                ('poll', models.ForeignKey(related_name='comments', to='voting.Poll')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_on'],
            },
        ),
        migrations.CreateModel(
            name='RadioPoll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.CharField(max_length=500)),
                ('poll', models.ForeignKey(related_name='radio_polls', to='voting.Poll')),
            ],
        ),
        migrations.CreateModel(
            name='RadioPollChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer', models.CharField(max_length=500)),
                ('votes', models.IntegerField(default=0)),
                ('radio_poll', models.ForeignKey(related_name='answers', to='voting.RadioPoll')),
            ],
            options={
                'ordering': ['radio_poll__question'],
            },
        ),
        migrations.CreateModel(
            name='RangePoll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=500)),
                ('poll', models.ForeignKey(related_name='range_polls', to='voting.Poll')),
            ],
        ),
        migrations.CreateModel(
            name='RangePollChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('votes', models.IntegerField(default=0)),
                ('nominee', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('range_poll', models.ForeignKey(related_name='choices', to='voting.RangePoll')),
            ],
            options={
                'ordering': ['nominee__first_name', 'nominee__last_name'],
            },
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_voted', models.DateField(auto_now_add=True)),
                ('poll', models.ForeignKey(to='voting.Poll')),
                ('user', models.ForeignKey(related_name='votes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='poll',
            name='users_voted',
            field=models.ManyToManyField(related_name='polls_voted', through='voting.Vote', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='poll',
            name='valid_groups',
            field=models.ForeignKey(related_name='valid_polls', to='auth.Group'),
        ),
    ]
