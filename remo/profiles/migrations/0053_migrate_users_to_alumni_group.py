# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models


class Migration(DataMigration):

    def forwards(self, orm):
        """Migrate users with no group to alumni group."""
        users = orm['auth.User'].objects.filter(groups__isnull=True)
        alumni_group = orm['auth.Group'].objects.get(name='Alumni')
        for user in users:
            user.groups.add(alumni_group)

    def backwards(self, orm):
        "Write your backwards methods here."
        users = orm['auth.User'].objects.filter(groups__name='Alumni')
        for user in users:
            user.groups.clear()

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'profiles.functionalarea': {
            'Meta': {'ordering': "['name']", 'object_name': 'FunctionalArea'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'blank': 'True'})
        },
        'profiles.useravatar': {
            'Meta': {'object_name': 'UserAvatar'},
            'avatar_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '400'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 1, 27, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'profiles.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'users_added'", 'null': 'True', 'to': "orm['auth.User']"}),
            'bio': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'current_streak_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_joined_program': ('django.db.models.fields.DateField', [], {'blank': 'True'}),
            'date_left_program': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'diaspora_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '50', 'blank': 'True'}),
            'facebook_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'first_report_notification': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'functional_areas': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users_matching'", 'symmetrical': 'False', 'to': "orm['profiles.FunctionalArea']"}),
            'gender': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'irc_channels': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'irc_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'is_rotm_nominee': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_unavailable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'jabber_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'linkedin_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'local_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'lon': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'longest_streak_end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'longest_streak_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'mentor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'mentees'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
            'mozillian_username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '40', 'blank': 'True'}),
            'mozillians_profile_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'personal_blog_feed': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'personal_website_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'private_email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '75', 'null': 'True'}),
            'receive_email_on_add_comment': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'receive_email_on_add_event_comment': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'receive_email_on_add_voting_comment': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'registration_complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'second_report_notification': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'tracked_functional_areas': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users_tracking'", 'symmetrical': 'False', 'to': "orm['profiles.FunctionalArea']"}),
            'twitter_account': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '16', 'blank': 'True'}),
            'unavailability_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'wiki_profile_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        },
        'profiles.userstatus': {
            'Meta': {'ordering': "['-expected_date', '-created_on']", 'object_name': 'UserStatus'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'expected_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'replacement_rep': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'replaced_rep'", 'null': 'True', 'to': "orm['auth.User']"}),
            'return_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'status'", 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['profiles']
    symmetrical = True
