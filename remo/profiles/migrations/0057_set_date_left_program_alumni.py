# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models


class Migration(DataMigration):

    def forwards(self, orm):
        """Set the date left program date.

        Set the date to the date of the last report, adding an
        offset of three months."""
        from django.core.exceptions import (MultipleObjectsReturned,
                                            ObjectDoesNotExist)

        alumni_users = orm['auth.User'].objects.filter(groups__name='Alumni')
        today = datetime.datetime.now()

        for alumni in alumni_users:
            if alumni.userprofile.date_left_program:
                continue

            report = None

            try:
                report = (orm['reports.NGReport'].objects.filter(user=alumni)
                          .latest('report_date'))
            except ObjectDoesNotExist:
                pass
            except MultipleObjectsReturned:
                report = orm['reports.NGReport'].filter(user=alumni)[0]

            if report:
                date_left = (datetime.datetime
                             .combine((report.report_date +
                                       datetime.timedelta(weeks=12)),
                                      datetime.datetime.min.time()))
                if date_left > today:
                    alumni.userprofile.date_left_program = today
                else:
                    alumni.userprofile.date_left_program = date_left
            else:
                alumni.userprofile.date_left_program = today
            alumni.userprofile.save()

    def backwards(self, orm):
        """Nothing to do here."""
        pass


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
        'dashboard.actionitem': {
            'Meta': {'ordering': "['-due_date', '-updated_on', '-created_on']", 'object_name': 'ActionItem'},
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'due_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'priority': ('django.db.models.fields.IntegerField', [], {}),
            'resolved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'action_items_assigned'", 'to': "orm['auth.User']"})
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
            'actual_attendance': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'attendees': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'events_attended'", 'symmetrical': 'False', 'through': "orm['events.Attendance']", 'to': "orm['auth.User']"}),
            'budget_bug': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'event_budget_requests'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['remozilla.Bug']"}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'events_categories'", 'symmetrical': 'False', 'to': "orm['profiles.FunctionalArea']"}),
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'converted_visitors': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'estimated_attendance': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'external_link': ('django.db.models.fields.URLField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'extra_content': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'goals': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'events_goals'", 'symmetrical': 'False', 'to': "orm['events.EventGoal']"}),
            'has_new_metrics': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hashtag': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {}),
            'metrics': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['events.EventMetric']", 'through': "orm['events.EventMetricOutcome']", 'symmetrical': 'False'}),
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
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'venue': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        'events.eventgoal': {
            'Meta': {'ordering': "['name']", 'object_name': 'EventGoal'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '127'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '127', 'blank': 'True'})
        },
        'events.eventmetric': {
            'Meta': {'ordering': "['name']", 'object_name': 'EventMetric'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'events.eventmetricoutcome': {
            'Meta': {'object_name': 'EventMetricOutcome'},
            'details': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Event']"}),
            'expected_outcome': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metric': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.EventMetric']"}),
            'outcome': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
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
            'last_update': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2015, 3, 1, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
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
            'jabber_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'linkedin_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'local_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'lon': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'longest_streak_end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'longest_streak_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'mentor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'mentees'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
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
            'is_unavailable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'replacement_rep': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'replaced_rep'", 'null': 'True', 'to': "orm['auth.User']"}),
            'return_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'status'", 'to': "orm['auth.User']"})
        },
        'remozilla.bug': {
            'Meta': {'ordering': "['-bug_last_change_time']", 'object_name': 'Bug'},
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bugs_assigned'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
            'budget_needinfo': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'}),
            'bug_creation_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'bug_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'}),
            'bug_last_change_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'cc': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'bugs_cced'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'component': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'council_member_assigned': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'council_vote_requested': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bugs_created'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
            'first_comment': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pending_mentor_validation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'verified_activity': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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

    complete_apps = ['reports', 'profiles']
    symmetrical = True
