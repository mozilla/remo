# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('due_date', models.DateField(null=True, blank=True)),
                ('priority', models.IntegerField(choices=[(1, b'Minor'), (2, b'Normal'), (3, b'Major'), (4, b'Critical'), (5, b'Blocker')])),
                ('resolved', models.BooleanField(default=False)),
                ('completed', models.BooleanField(default=False)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(related_name='action_items_assigned', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-due_date', '-updated_on', '-created_on'],
            },
        ),
    ]
