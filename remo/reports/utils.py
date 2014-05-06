from datetime import datetime

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.timezone import now

from remo.base.tasks import send_remo_mail
from remo.base.utils import get_date
from remo.reports.models import NGReport


def count_user_ng_reports(user, current_streak=False,
                          longest_streak=False, period=0):
    """Return the number of reports of a user over

    a period of time. If current_streak is True return the
    current streak of a user. Arg period expects weeks
    eg 2 means 2 * 7 = 14 days.
    """
    end_period = now()
    start_period = datetime(2011, 01, 01)

    if current_streak:
        start_period = user.userprofile.current_streak_start
    elif longest_streak:
        start_period = user.userprofile.longest_streak_start
        end_period = user.userprofile.longest_streak_end
    elif period > 0:
        start_period = get_date(-(period * 7))

    query = user.ng_reports.filter(report_date__range=(start_period,
                                                       end_period))

    return query.count()


def get_last_report(user):
    """Return user's last report in the past."""
    today = now().date()

    try:
        reports = user.ng_reports.filter(report_date__lte=today)
        return reports.latest('report_date')
    except NGReport.DoesNotExist:
        return None


def send_report_notification(reps, weeks):
    """Send notification to inactive reps."""
    rep_subject = '[Reminder] Please share your recent activities'
    rep_mail_body = 'emails/reps_ng_report_notification.txt'
    mentor_subject = ('[Report] Mentee without report for the last %d weeks'
                      % weeks)
    mentor_mail_body = 'emails/mentor_ng_report_notification.txt'

    for rep in reps:
        ctx_data = {'mentor': rep.userprofile.mentor,
                    'user': rep,
                    'SITE_URL': settings.SITE_URL,
                    'weeks': weeks}

        rep_message = render_to_string(rep_mail_body, ctx_data)
        mentor_message = render_to_string(mentor_mail_body, ctx_data)
        send_remo_mail.delay(rep_subject, [rep.email], message=rep_message)
        send_remo_mail.delay(mentor_subject, [rep.userprofile.mentor.email],
                             message=mentor_message)
