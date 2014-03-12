# -*- coding: utf-8 -*-
import datetime

from datetime import date, timedelta

from south.db import db
from south.v2 import DataMigration
from django.db import models

from remo.events.helpers import get_event_link
from remo.reports import ACTIVITY_EVENT_ATTEND, ACTIVITY_EVENT_CREATE


class Migration(DataMigration):
    depends_on = (
        ('events', '0011_auto_categories.py'),
        ('profiles', '0041_auto__del_field_userprofile_receive_email_on_edit_report__del_field_us.py')
    )

    def forwards(self, orm):
        """Data migration from old report system to continuous reporting."""
        Activity = orm['reports.Activity']
        Attendance = orm['events.Attendance']
        Event = orm['events.Event']
        NGReport = orm['reports.NGReport']
        Report = orm['reports.Report']
        UserProfile = orm['profiles.UserProfile']

        event_attendance = Activity.objects.get(name=ACTIVITY_EVENT_ATTEND)
        event_creation = Activity.objects.get(name=ACTIVITY_EVENT_CREATE)
        month_planning = Activity.objects.get_or_create(name='Month planning')[0]
        month_recap = Activity.objects.get_or_create(name='Month recap')[0]
        recruitment_effort = Activity.objects.get_or_create(name='Recruitment effort')[0]

        # Delete all temporary NGReport objects
        NGReport.objects.all().delete()

        # Delete streak data from user profiles
        for profile in UserProfile.objects.all():
            profile.current_streak_start = None
            profile.longest_streak_start = None
            profile.longest_streak_end = None
            profile.save()

        # Migrate events in old reports each one in a new report
        for event in Event.objects.all():
            args = {}
            args['user'] = event.owner
            args['report_date'] = event.start.date()
            args['mentor'] = event.owner.userprofile.mentor
            args['activity'] = event_creation
            args['longitude'] = event.lon
            args['latitude'] = event.lat
            args['location'] = '%s, %s, %s' % (event.city,
                                               event.region,
                                               event.country)
            args['event'] = event
            args['link'] = get_event_link(event)
            args['activity_description'] = event.description
            args['is_passive'] = True
            try:
                report = NGReport.objects.create(**args)
                report.functional_areas.add(*event.categories.all())
            except Exception as e:
                print 'Error encountered while migrating Event object: %d' % event.id
                print e

            for attendance in Attendance.objects.filter(event=event,
                                                        user__groups__name='Rep'):
                args = {}
                args['user'] = attendance.user
                args['report_date'] = attendance.event.start.date()
                args['mentor'] = attendance.user.userprofile.mentor
                args['activity'] = event_attendance
                args['longitude'] = attendance.event.lon
                args['latitude'] = attendance.event.lat
                args['location'] = '%s, %s, %s' % (attendance.event.city,
                                                   attendance.event.region,
                                                   attendance.event.country)
                args['event'] = attendance.event
                args['link'] = get_event_link(attendance.event)
                args['activity_description'] = attendance.event.description
                args['is_passive'] = True
                try:
                    report = NGReport.objects.create(**args)
                    report.functional_areas.add(*attendance.event.categories.all())
                except Exception as e:
                    print 'Error encountered while migrating Report object: %d' % attendance.id
                    print e

        for report in Report.objects.all():
            # Migrate recruit_comment to a new activity: "Recruitment effort"
            if report.recruits_comments:
                year = report.month.year
                month = report.month.month
                args = {}
                args['user'] = report.user
                args['report_date'] = date(year, month, 1) - timedelta(days=1)
                args['mentor'] = report.mentor
                args['activity'] = recruitment_effort
                args['longitude'] = report.user.userprofile.lon
                args['latitude'] = report.user.userprofile.lat
                args['location'] = '%s, %s, %s' % (report.user.userprofile.city,
                                                   report.user.userprofile.region,
                                                   report.user.userprofile.country)
                args['activity_description'] = report.recruits_comments
                try:
                    ngreport = NGReport.objects.create(**args)
                    ngreport.functional_areas.add(*report.user.userprofile.functional_areas.all())
                except Exception as e:
                    print 'Error encountered while migrating Report object: %d' % report.id
                    print e

            # Migrate past activities to a new activity: "Month Recap"
            if report.past_items:
                year = report.month.year
                month = report.month.month
                args = {}
                args['user'] = report.user
                args['report_date'] = date(year, month, 1) - timedelta(days=1)
                args['mentor'] = report.mentor
                args['activity'] = month_recap
                args['longitude'] = report.user.userprofile.lon
                args['latitude'] = report.user.userprofile.lat
                args['location'] = '%s, %s, %s' % (report.user.userprofile.city,
                                                   report.user.userprofile.region,
                                                   report.user.userprofile.country)
                args['activity_description'] = report.past_items
                try:
                    ngreport = NGReport.objects.create(**args)
                    ngreport.functional_areas.add(*report.user.userprofile.functional_areas.all())
                except Exception as e:
                    print 'Error encountered while migrating Report object: %d' % report.id
                    print e

            # Migrate future activities to a new activity: "Month planning"
            if report.future_items:
                args = {}
                args['user'] = report.user
                args['report_date'] = report.month
                args['mentor'] = report.mentor
                args['activity'] = month_planning
                args['longitude'] = report.user.userprofile.lon
                args['latitude'] = report.user.userprofile.lat
                args['location'] = '%s, %s, %s' % (report.user.userprofile.city,
                                                   report.user.userprofile.region,
                                                   report.user.userprofile.country)
                args['activity_description'] = report.future_items
                try:
                    ngreport = NGReport.objects.create(**args)
                    ngreport.functional_areas.add(*report.user.userprofile.functional_areas.all())
                except Exception as e:
                    print 'Error encountered while migrating Report object: %d' % report.id
                    print e

            # Migrate report activities with links
            for activity in report.reportlink_set.all():
                year = report.month.year
                month = report.month.month
                args = {}
                args['user'] = activity.report.user
                args['report_date'] = date(year, month, 1) - timedelta(days=1)
                args['mentor'] = activity.report.mentor
                args['activity'] = month_recap
                args['longitude'] = activity.report.user.userprofile.lon
                args['latitude'] = activity.report.user.userprofile.lat
                args['location'] = '%s, %s, %s' % (activity.report.user.userprofile.city,
                                                   activity.report.user.userprofile.region,
                                                   activity.report.user.userprofile.country)
                args['link'] = activity.link
                args['link_description'] = activity.description
                try:
                    ngreport = NGReport.objects.create(**args)
                    ngreport.functional_areas.add(*report.user.userprofile.functional_areas.all())
                except Exception as e:
                    print 'Error encountered while migrating ReportLink objects: %d' % activity.id
                    print e

    def backwards(self, orm):
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
        'events.eventcomment': {
            'Meta': {'ordering': "['id']", 'object_name': 'EventComment'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'events.metric': {
            'Meta': {'object_name': 'Metric'},
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'metrics'", 'to': "orm['events.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'outcome': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'})
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
            'last_update': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 3, 10, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
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
            'diaspora_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '50', 'blank': 'True'}),
            'facebook_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'functional_areas': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users_matching'", 'symmetrical': 'False', 'to': "orm['profiles.FunctionalArea']"}),
            'gender': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'irc_channels': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'irc_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'jabber_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'last_report_notification': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
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
            'region': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'registration_complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tracked_functional_areas': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users_tracking'", 'symmetrical': 'False', 'to': "orm['profiles.FunctionalArea']"}),
            'twitter_account': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '16', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'wiki_profile_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200'})
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ng_reports'", 'to': "orm['auth.User']"})
        },
        'reports.ngreportcomment': {
            'Meta': {'ordering': "['id']", 'object_name': 'NGReportComment'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reports.NGReport']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': "orm['auth.User']"})
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
            'link': ('django.db.models.fields.URLField', [], {'max_length': '500'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'participation_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reports.Report']"})
        },
        'reports.reportlink': {
            'Meta': {'object_name': 'ReportLink'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reports.Report']"})
        }
    }

    complete_apps = ['profiles', 'events', 'reports']
    symmetrical = True
