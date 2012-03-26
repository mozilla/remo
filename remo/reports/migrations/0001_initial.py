# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Report'
        db.create_table('reports_report', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('mentor', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='reports_mentored', null=True, to=orm['auth.User'])),
            ('month', self.gf('django.db.models.fields.DateField')()),
            ('empty', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('recruits_comments', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('past_items', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('future_items', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('flags', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('overdue', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('reports', ['Report'])

        # Adding unique constraint on 'Report', fields ['user', 'month']
        db.create_unique('reports_report', ['user_id', 'month'])

        # Adding model 'ReportComment'
        db.create_table('reports_reportcomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reports.Report'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('reports', ['ReportComment'])

        # Adding model 'ReportEvent'
        db.create_table('reports_reportevent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reports.Report'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('description', self.gf('django.db.models.fields.TextField')(default='')),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('participation_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('reports', ['ReportEvent'])

        # Adding model 'ReportLink'
        db.create_table('reports_reportlink', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reports.Report'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('reports', ['ReportLink'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Report', fields ['user', 'month']
        db.delete_unique('reports_report', ['user_id', 'month'])

        # Deleting model 'Report'
        db.delete_table('reports_report')

        # Deleting model 'ReportComment'
        db.delete_table('reports_reportcomment')

        # Deleting model 'ReportEvent'
        db.delete_table('reports_reportevent')

        # Deleting model 'ReportLink'
        db.delete_table('reports_reportlink')


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
            'password': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
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
        'reports.report': {
            'Meta': {'ordering': "['-month']", 'unique_together': "(['user', 'month'],)", 'object_name': 'Report'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'empty': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flags': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'future_items': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mentor': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'reports_mentored'", 'null': 'True', 'to': "orm['auth.User']"}),
            'month': ('django.db.models.fields.DateField', [], {}),
            'overdue': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'past_items': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'recruits_comments': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'reports.reportcomment': {
            'Meta': {'ordering': "['id']", 'object_name': 'ReportComment'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reports.Report']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'reports.reportevent': {
            'Meta': {'object_name': 'ReportEvent'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'participation_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reports.Report']"})
        },
        'reports.reportlink': {
            'Meta': {'object_name': 'ReportLink'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reports.Report']"})
        }
    }

    complete_apps = ['reports']
