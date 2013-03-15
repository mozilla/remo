# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Poll.task_start_id'
        db.add_column('voting_poll', 'task_start_id',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=256, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Poll.task_end_id'
        db.add_column('voting_poll', 'task_end_id',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=256, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Poll.last_notification'
        db.add_column('voting_poll', 'last_notification',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)


        # Changing field 'Poll.created_on'
        db.alter_column('voting_poll', 'created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

    def backwards(self, orm):
        # Deleting field 'Poll.task_start_id'
        db.delete_column('voting_poll', 'task_start_id')

        # Deleting field 'Poll.task_end_id'
        db.delete_column('voting_poll', 'task_end_id')

        # Deleting field 'Poll.last_notification'
        db.delete_column('voting_poll', 'last_notification')


        # Changing field 'Poll.created_on'
        db.alter_column('voting_poll', 'created_on', self.gf('django.db.models.fields.DateField')(auto_now_add=True))

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
        'voting.poll': {
            'Meta': {'ordering': "['-created_on']", 'object_name': 'Poll'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'range_polls_created'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_notification': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'task_end_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'task_start_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'users_voted': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'polls_voted'", 'symmetrical': 'False', 'through': "orm['voting.Vote']", 'to': "orm['auth.User']"}),
            'valid_groups': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'valid_polls'", 'to': "orm['auth.Group']"})
        },
        'voting.radiopoll': {
            'Meta': {'object_name': 'RadioPoll'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'radio_polls'", 'to': "orm['voting.Poll']"}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'voting.radiopollchoice': {
            'Meta': {'ordering': "['-votes']", 'object_name': 'RadioPollChoice'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'radio_poll': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answers'", 'to': "orm['voting.RadioPoll']"}),
            'votes': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'voting.rangepoll': {
            'Meta': {'object_name': 'RangePoll'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'range_polls'", 'to': "orm['voting.Poll']"})
        },
        'voting.rangepollchoice': {
            'Meta': {'ordering': "['-votes', 'nominee__last_name', 'nominee__first_name']", 'object_name': 'RangePollChoice'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nominee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'range_poll': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'choices'", 'to': "orm['voting.RangePoll']"}),
            'votes': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'voting.vote': {
            'Meta': {'object_name': 'Vote'},
            'date_voted': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['voting.Poll']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['voting']