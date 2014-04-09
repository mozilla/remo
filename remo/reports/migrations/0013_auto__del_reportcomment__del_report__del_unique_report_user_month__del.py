# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    no_dry_run = True

    def forwards(self, orm):
        # Removing unique constraint on 'Report', fields ['user', 'month']
        db.delete_unique('reports_report', ['user_id', 'month'])

        # Deleting model 'ReportComment'
        db.delete_table('reports_reportcomment')

        # Deleting model 'Report'
        db.delete_table('reports_report')

        # Deleting model 'ReportLink'
        db.delete_table('reports_reportlink')

        # Deleting model 'ReportEvent'
        db.delete_table('reports_reportevent')

        # Delete ContentTypes and Permissions
        orm['contenttypes.contenttype'].objects.filter(app_label='reports', model='report').delete()
        orm['contenttypes.contenttype'].objects.filter(app_label='reports', model='reportcomment').delete()
        orm['contenttypes.contenttype'].objects.filter(app_label='reports', model='reportlink').delete()
        orm['contenttypes.contenttype'].objects.filter(app_label='reports', model='reportevent').delete()

    def backwards(self, orm):
        # Adding model 'ReportComment'
        db.create_table('reports_reportcomment', (
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reports.Report'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('reports', ['ReportComment'])

        # Adding model 'Report'
        db.create_table('reports_report', (
            ('month', self.gf('django.db.models.fields.DateField')()),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reports', to=orm['auth.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('future_items', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('past_items', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('recruits_comments', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('flags', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('mentor', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='reports_mentored', null=True, to=orm['auth.User'])),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('empty', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('overdue', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('reports', ['Report'])

        # Adding unique constraint on 'Report', fields ['user', 'month']
        db.create_unique('reports_report', ['user_id', 'month'])

        # Adding model 'ReportLink'
        db.create_table('reports_reportlink', (
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reports.Report'])),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('reports', ['ReportLink'])

        # Adding model 'ReportEvent'
        db.create_table('reports_reportevent', (
            ('participation_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('description', self.gf('django.db.models.fields.TextField')(default='')),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=500)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reports.Report'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=300)),
        ))
        db.send_create_signal('reports', ['ReportEvent'])

        # We won't restore content types or permissions here. We will
        # let Django do it following models definitions.


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
        'events.attendance': {
            'Meta': {'object_name': 'Attendance'},
            'date_subscribed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'events.event': {
            'Meta': {'ordering': "['start']", 'object_name': 'Event'},
            'attendees': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'events_attended'", 'symmetrical': 'False', 'through': "orm['events.Attendance']", 'to': "orm['auth.User']"}),
            'budget_bug': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'event_budget_requests'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['remozilla.Bug']"}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'events_categories'", 'symmetrical': 'False', 'to': "orm['profiles.FunctionalArea']"}),
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'converted_visitors': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'estimated_attendance': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'external_link': ('django.db.models.fields.URLField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'extra_content': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'goals': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'events_goals'", 'symmetrical': 'False', 'to': "orm['events.EventGoal']"}),
            'hashtag': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {}),
            'mozilla_event': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events_created'", 'to': "orm['auth.User']"}),
            'planning_pad_url': ('django.db.models.fields.URLField', [], {'max_length': '300', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'swag_bug': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'event_swag_requests'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['remozilla.Bug']"}),
            'times_edited': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'timezone': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'venue': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        'events.eventgoal': {
            'Meta': {'ordering': "['name']", 'object_name': 'EventGoal'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '127'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '127', 'blank': 'True'})
        },
        'profiles.functionalarea': {
            'Meta': {'ordering': "['name']", 'object_name': 'FunctionalArea'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'blank': 'True'})
        },
        'remozilla.bug': {
            'Meta': {'ordering': "['-bug_last_change_time']", 'object_name': 'Bug'},
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bugs_assigned'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
            'bug_creation_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'bug_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'}),
            'bug_last_change_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'cc': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'bugs_cced'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'component': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'council_vote_requested': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bugs_created'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
            'first_comment': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resolution': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '30'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '30'}),
            'summary': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'whiteboard': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500'})
        },
        'reports.activity': {
            'Meta': {'ordering': "['name']", 'object_name': 'Activity'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'reports.campaign': {
            'Meta': {'ordering': "['name']", 'object_name': 'Campaign'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'reports.ngreport': {
            'Meta': {'ordering': "['-report_date', '-created_on']", 'object_name': 'NGReport'},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ng_reports'", 'to': "orm['reports.Activity']"}),
            'activity_description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ng_reports'", 'null': 'True', 'to': "orm['reports.Campaign']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Event']", 'null': 'True', 'blank': 'True'}),
            'functional_areas': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'ng_reports'", 'symmetrical': 'False', 'to': "orm['profiles.FunctionalArea']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_passive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '500', 'blank': 'True'}),
            'link_description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '500', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '150', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'mentor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ng_reports_mentored'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
            'report_date': ('django.db.models.fields.DateField', [], {}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ng_reports'", 'to': "orm['auth.User']"}),
            'verified_recruitment': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'reports.ngreportcomment': {
            'Meta': {'ordering': "['id']", 'object_name': 'NGReportComment'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reports.NGReport']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['reports']
