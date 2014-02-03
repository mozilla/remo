from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import render_to_string

from celery.task import task

from remo.reports import ACTIVITY_EVENT_ATTEND, ACTIVITY_EVENT_CREATE


DIGEST_SUBJECT = 'Your mentee activity for {date}'


@task()
def send_remo_mail(user_ids_list, subject, email_template, data=None):
    """Send to user_list emails based rendered using email_template
    and populated with data.

    """
    if not data:
        data = {}

    data.update({'SITE_URL': settings.SITE_URL,
                 'FROM_EMAIL': settings.FROM_EMAIL})

    for user_id in user_ids_list:
        if User.objects.filter(pk=user_id).exists():
            user = User.objects.get(pk=user_id)
            ctx_data = {'user': user,
                        'userprofile': user.userprofile}
            ctx_data.update(data)
            message = render_to_string(email_template, ctx_data)
            send_mail(subject, message, settings.FROM_EMAIL, [user.email])


@task()
def send_report_digest():
    from remo.reports.models import NGReport
    today = datetime.utcnow().date()
    # This would include reports created today about past events or
    # non-events, and reports created in the past for events that
    # occurred today, but not reports created today for future events
    reports = NGReport.objects.filter(Q(created_on__year=today.year,
                                        created_on__month=today.month,
                                        created_on__day=today.day,
                                        report_date__lte=today) |
                                      Q(report_date=today,
                                        activity__name__in=[
                                            ACTIVITY_EVENT_CREATE,
                                            ACTIVITY_EVENT_ATTEND]))
    reports = reports.distinct()
    # Since MySQL doesn't support distinct(field), we have to dedup
    # the list in python.
    mentors = set(reports.exclude(mentor__isnull=True)
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
        message = render_to_string('emails/report_digest.txt', ctx_data)
        # Manually replace quotes and double-quotes as these get
        # escaped by the template and this makes the message look bad.
        message = message.replace('&#34;', '"').replace('&#39;', "'")
        send_mail(subject, message, settings.FROM_EMAIL, [mentor.email])
