# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FeaturedRep',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(null=True, blank=True)),
                ('updated_on', models.DateTimeField(null=True, blank=True)),
                ('text', models.TextField()),
                ('created_by', models.ForeignKey(related_name='reps_featured', to=settings.AUTH_USER_MODEL)),
                ('users', models.ManyToManyField(related_name='featuredrep_users', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_on'],
                'get_latest_by': 'updated_on',
                'permissions': (('can_edit_featured', 'Can edit featured reps'), ('can_delete_featured', 'Can delete featured reps')),
            },
        ),
    ]
