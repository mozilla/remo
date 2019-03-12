from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.timezone import make_aware, now

import pytz

from django_statsd.clients import statsd

from remo.base.utils import get_date
from remo.celery import app
from remo.dashboard.models import ActionItem
from remo.reports import ACTIVITY_EVENT_ATTEND, ACTIVITY_EVENT_CREATE
from remo.reports.utils import send_report_notification


DIGEST_SUBJECT = 'Your mentee activity for {date}'


@app.task
def send_report_digest():
    from remo.reports.models import NGReport
    today = now().date()
    # This would include reports created today about past events or
    # non-events, and reports created in the past for events that
    # occurred today, but not reports created today for future events
    query_start = make_aware(datetime.combine(today, datetime.min.time()), pytz.UTC)
    query_end = make_aware(datetime.combine(today, datetime.max.time()), pytz.UTC)
    reports = NGReport.objects.filter(Q(created_on__range=[query_start, query_end],
                                        report_date__lte=today)
                                      | Q(report_date=today,
                                          activity__name__in=[
                                              ACTIVITY_EVENT_CREATE,
                                              ACTIVITY_EVENT_ATTEND
                                          ]))
    reports = reports.distinct()
    # Since MySQL doesn't support distinct(field), we have to dedup
    # the list in python.
    mentors = set(reports.exclude(mentor__isnull=True)
                  .exclude(mentor__groups__name='Alumni')
                  .values_list('mentor', flat=True))
    for mentor_id in mentors:
        mentor = User.objects.get(id=mentor_id)
        reports_for_mentor = reports.filter(mentor=mentor)
        if not reports_for_mentor.exists():
            continue
        datestring = today.strftime('%a %d %b %Y')
        subject = DIGEST_SUBJECT.format(date=datestring)
        ctx_data = {'mentor': mentor,
                    'reports': reports_for_mentor,
                    'datestring': datestring}
        message = render_to_string('emails/report_digest.jinja', ctx_data)
        # Manually replace quotes and double-quotes as these get
        # escaped by the template and this makes the message look bad.
        message = message.replace('&#34;', '"').replace('&#39;', "'")
        send_mail(subject, message, settings.FROM_EMAIL, [mentor.email])


@app.task
def send_first_report_notification():
    """Send inactivity notification after 4 weeks."""
    today = get_date()
    start = today - timedelta(weeks=4)
    end = today + timedelta(weeks=4)
    users = User.objects.filter(
        groups__name='Rep',
        userprofile__registration_complete=True,
        userprofile__first_report_notification__isnull=True)

    # Exclude users with a report filed between start and end period
    # and users who joined the program less than one month
    inactive_users = (users
                      .exclude(ng_reports__report_date__range=[start, end])
                      .exclude(userprofile__date_joined_program__gt=start)
                      .exclude(status__is_unavailable=True))

    send_report_notification(inactive_users, weeks=4)
    for user in inactive_users:
        user.userprofile.first_report_notification = today
        user.userprofile.save()
    statsd.incr('reports.send_first_report_notification')


@app.task
def send_second_report_notification():
    """Send inactivity notification after 8 weeks."""
    today = get_date()
    start = today - timedelta(weeks=8)
    end = today + timedelta(weeks=8)
    users = User.objects.filter(
        groups__name='Rep',
        userprofile__registration_complete=True,
        userprofile__first_report_notification__lte=today - timedelta(weeks=4),
        userprofile__second_report_notification__isnull=True)
    # Exclude users with a report filed between start and end period
    # and users who joined the program less than one month
    inactive_users = (users
                      .exclude(ng_reports__report_date__range=[start, end])
                      .exclude(userprofile__date_joined_program__gt=start)
                      .exclude(status__is_unavailable=True))

    send_report_notification(inactive_users, weeks=8)
    for user in inactive_users:
        user.userprofile.second_report_notification = today
        user.userprofile.save()
    statsd.incr('reports.send_second_report_notification')


@app.task
def zero_current_streak():
    """Zero current streak.

    Zero current streak for users without a report in the last week.
    """

    reps = User.objects.filter(
        ~Q(ng_reports__report_date__range=[get_date(-7), get_date()]),
        groups__name='Rep')

    for rep in reps:
        rep.userprofile.current_streak_start = None
        rep.userprofile.save()


@app.task
def calculate_longest_streaks():
    """Calculate user's longest streaks."""
    from remo.reports.models import NGReport

    # Calculate the longest streak only for the users that
    # submitted a report today and already have a longest streak.
    reps = (User.objects.filter(
        groups__name='Rep', ng_reports__created_on__range=[get_date(), now()])
        .exclude(userprofile__longest_streak_start=None)
        .exclude(userprofile__longest_streak_end=None))

    for rep in reps:
        streak_count = 0
        longest_start = None
        longest_end = None
        reports = NGReport.objects.filter(user=rep).order_by('report_date')

        if reports:
            start = reports[0].report_date
            end = reports[0].report_date

            for report in reports:
                try:
                    next_report = report.get_next_by_report_date(user=rep)
                except NGReport.DoesNotExist:
                    if (end - start).days > streak_count:
                        longest_start = start
                        longest_end = end
                    break

                if (next_report.report_date - report.report_date).days > 7:
                    if (end - start).days > streak_count:
                        streak_count = (end - start).days
                        longest_start = start
                        longest_end = end
                    start = next_report.report_date
                end = next_report.report_date

        rep.userprofile.longest_streak_start = longest_start
        rep.userprofile.longest_streak_end = longest_end
        rep.userprofile.save()


@app.task
def resolve_report_action_items():
    """Resolve any action items.

    Mark all unresolved action items with due_date the today date as resolved.
    """
    from remo.reports.models import NGReport

    action_model = ContentType.objects.get_for_model(NGReport)
    items = ActionItem.objects.filter(content_type=action_model,
                                      resolved=False,
                                      due_date=now().date())
    items.update(resolved=True)
