# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Poll'
        db.create_table('voting_poll', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=100, blank=True)),
            ('start', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')()),
            ('eligimate_groups', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('created_on', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='polls_range_created', to=orm['auth.User'])),
        ))
        db.send_create_signal('voting', ['Poll'])

        # Adding model 'Vote'
        db.create_table('voting_vote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('ranged_poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.Poll'])),
            ('date_voted', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('voting', ['Vote'])

        # Adding model 'PollRange'
        db.create_table('voting_pollrange', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.Poll'])),
        ))
        db.send_create_signal('voting', ['PollRange'])

        # Adding model 'PollRangeVotes'
        db.create_table('voting_pollrangevotes', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('votes', self.gf('django.db.models.fields.IntegerField')()),
            ('poll_range', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.PollRange'])),
            ('nominee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('voting', ['PollRangeVotes'])

        # Adding model 'PollRadio'
        db.create_table('voting_pollradio', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.Poll'])),
        ))
        db.send_create_signal('voting', ['PollRadio'])

        # Adding model 'PollChoices'
        db.create_table('voting_pollchoices', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('votes', self.gf('django.db.models.fields.IntegerField')()),
            ('radio_poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.PollRadio'])),
        ))
        db.send_create_signal('voting', ['PollChoices'])


    def backwards(self, orm):
        # Deleting model 'Poll'
        db.delete_table('voting_poll')

        # Deleting model 'Vote'
        db.delete_table('voting_vote')

        # Deleting model 'PollRange'
        db.delete_table('voting_pollrange')

        # Deleting model 'PollRangeVotes'
        db.delete_table('voting_pollrangevotes')

        # Deleting model 'PollRadio'
        db.delete_table('voting_pollradio')

        # Deleting model 'PollChoices'
        db.delete_table('voting_pollchoices')


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
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'polls_range_created'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'eligimate_groups': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'end': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {}),
            'users_voted': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'polls_voted'", 'symmetrical': 'False', 'through': "orm['voting.Vote']", 'to': "orm['auth.User']"})
        },
        'voting.pollchoices': {
            'Meta': {'object_name': 'PollChoices'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'radio_poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['voting.PollRadio']"}),
            'votes': ('django.db.models.fields.IntegerField', [], {})
        },
        'voting.pollradio': {
            'Meta': {'object_name': 'PollRadio'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['voting.Poll']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'voting.pollrange': {
            'Meta': {'object_name': 'PollRange'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nominees': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'polls_nominated'", 'symmetrical': 'False', 'through': "orm['voting.PollRangeVotes']", 'to': "orm['auth.User']"}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['voting.Poll']"})
        },
        'voting.pollrangevotes': {
            'Meta': {'object_name': 'PollRangeVotes'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nominee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'poll_range': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['voting.PollRange']"}),
            'votes': ('django.db.models.fields.IntegerField', [], {})
        },
        'voting.vote': {
            'Meta': {'object_name': 'Vote'},
            'date_voted': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ranged_poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['voting.Poll']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['voting']