# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'PollRadio'
        db.delete_table('voting_pollradio')

        # Deleting model 'PollChoices'
        db.delete_table('voting_pollchoices')

        # Deleting model 'PollRangeVotes'
        db.delete_table('voting_pollrangevotes')

        # Deleting model 'PollRange'
        db.delete_table('voting_pollrange')

        # Adding model 'RangePoll'
        db.create_table('voting_rangepoll', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=500)),
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.Poll'])),
        ))
        db.send_create_signal('voting', ['RangePoll'])

        # Adding model 'RadioPollChoice'
        db.create_table('voting_radiopollchoice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('votes', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('radio_poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.RadioPoll'])),
        ))
        db.send_create_signal('voting', ['RadioPollChoice'])

        # Adding model 'RangePollChoice'
        db.create_table('voting_rangepollchoice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('votes', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('range_poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.RangePoll'])),
            ('nominee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('voting', ['RangePollChoice'])

        # Adding model 'RadioPoll'
        db.create_table('voting_radiopoll', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.Poll'])),
        ))
        db.send_create_signal('voting', ['RadioPoll'])

        # Deleting field 'Vote.ranged_poll'
        db.delete_column('voting_vote', 'ranged_poll_id')

        # Adding field 'Vote.poll'
        db.add_column('voting_vote', 'poll',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['voting.Poll']),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'PollRadio'
        db.create_table('voting_pollradio', (
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.Poll'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=500)),
        ))
        db.send_create_signal('voting', ['PollRadio'])

        # Adding model 'PollChoices'
        db.create_table('voting_pollchoices', (
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('radio_poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.PollRadio'])),
            ('votes', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('voting', ['PollChoices'])

        # Adding model 'PollRangeVotes'
        db.create_table('voting_pollrangevotes', (
            ('votes', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nominee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('poll_range', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.PollRange'])),
        ))
        db.send_create_signal('voting', ['PollRangeVotes'])

        # Adding model 'PollRange'
        db.create_table('voting_pollrange', (
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['voting.Poll'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=500)),
        ))
        db.send_create_signal('voting', ['PollRange'])

        # Deleting model 'RangePoll'
        db.delete_table('voting_rangepoll')

        # Deleting model 'RadioPollChoice'
        db.delete_table('voting_radiopollchoice')

        # Deleting model 'RangePollChoice'
        db.delete_table('voting_rangepollchoice')

        # Deleting model 'RadioPoll'
        db.delete_table('voting_radiopoll')

        # Adding field 'Vote.ranged_poll'
        db.add_column('voting_vote', 'ranged_poll',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['voting.Poll']),
                      keep_default=False)

        # Deleting field 'Vote.poll'
        db.delete_column('voting_vote', 'poll_id')


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
            'created_on': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'users_voted': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'polls_voted'", 'symmetrical': 'False', 'through': "orm['voting.Vote']", 'to': "orm['auth.User']"}),
            'valid_groups': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'valid_polls'", 'to': "orm['auth.Group']"})
        },
        'voting.radiopoll': {
            'Meta': {'object_name': 'RadioPoll'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['voting.Poll']"}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'voting.radiopollchoice': {
            'Meta': {'ordering': "['-votes']", 'object_name': 'RadioPollChoice'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'radio_poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['voting.RadioPoll']"}),
            'votes': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'voting.rangepoll': {
            'Meta': {'object_name': 'RangePoll'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['voting.Poll']"})
        },
        'voting.rangepollchoice': {
            'Meta': {'ordering': "['-votes', 'nominee__last_name', 'nominee__first_name']", 'object_name': 'RangePollChoice'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nominee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'range_poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['voting.RangePoll']"}),
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