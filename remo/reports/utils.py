from datetime import date, datetime, timedelta

from django.core.urlresolvers import reverse
from django.utils.timezone import now as utc_now

from remo.base.utils import (get_object_or_none, go_back_n_months,
                             go_fwd_n_months, number2month)

from helpers import get_mentees, get_report_view_url
from models import PARTICIPATION_TYPE_CHOICES, Report

REPORTS_PERMISSION_LEVEL = {'owner': 3,
                            'authenticated': 2,
                            'anonymous': 1}


def get_month_first_report(user):
    """Return the month that we should get the first report from a Rep."""
    date_joined = user.userprofile.date_joined_program
    return go_fwd_n_months(date_joined, first_day=True)


def get_reports_for_year(user, start_year, end_year=None, allow_empty=False,
                         permission=REPORTS_PERMISSION_LEVEL['anonymous']):
    """Return a list of reports for year."""
    reports_list = {}
    tmp_date = datetime.today()
    up = user.userprofile
    today = datetime(year=tmp_date.year, month=tmp_date.month, day=1)
    date_joined = up.date_joined_program
    month_first_report = get_month_first_report(user)

    if not end_year:
        end_year = start_year

    for year in range(max(start_year, date_joined.year), end_year + 1):
        reports = user.reports.filter(month__year=year)

        reports_list[year] = []

        for month in range(1, 13):
            month = datetime(year=year, month=month, day=1)
            month_details = {'name': number2month(month.month,
                                                  full_name=False),
                             'fullname': number2month(month.month,
                                                      full_name=True)}

            if ((reports.filter(month=month).exists() and
                 ((permission > 1 and month >= today) or (month < today)))):
                report = reports.get(month=month)
                month_details['report'] = report
                month_details['class'] = 'exists'
                month_details['link'] = get_report_view_url(report)
            else:
                month_details['report'] = None

                if ((permission < 3 or month_first_report > month or
                     month > today)):
                    month_details['class'] = 'unavailable'
                    month_details['link'] = '#'
                else:
                    month_details['class'] = 'editable'
                    link = reverse('reports_edit_report',
                                   kwargs={'display_name': up.display_name,
                                           'year': year,
                                           'month': month_details['fullname']})
                    month_details['link'] = link

            reports_list[year].append(month_details)

    return reports_list


def get_mentee_reports_for_month(user, dateobj=None):
    """Return a dictionary with Mentee reports for month in dateobj.

    If dateobj==None return the reports of the previous month.

    """
    if not dateobj:
        one_month_before = go_back_n_months(date.today(), first_day=True)
    else:
        one_month_before = dateobj
    two_months_before = go_back_n_months(one_month_before, first_day=True)

    mentees = get_mentees(user)
    mentees_list = {'month': one_month_before.strftime("%B %Y"), 'reports': []}

    for mentee in mentees:
        month_first_report = get_month_first_report(mentee)
        current_report = get_object_or_none(Report, user=mentee,
                                            month=one_month_before)
        previous_report = get_object_or_none(Report, user=mentee,
                                             month=two_months_before)
        if not previous_report and two_months_before >= month_first_report:
            status = 'notfilled'
        elif current_report and current_report.empty:
            status = 'empty'
        else:
            status = ''

        mentees_list['reports'].append({'user': mentee, 'status': status,
                                        'report': current_report})

    return mentees_list


def participation_type_to_number(participation_type):
    """Convert participation type text to PARTICIPATION_TYPE_CHOICES number."""
    for number, name in PARTICIPATION_TYPE_CHOICES:
        if participation_type == name:
            return number


def count_user_ng_reports(user, current_streak=False,
                          longest_streak=False, period=0):
    """Return the number of reports of a user over

    a period of time. If current_streak is True return the
    current streak of a user. Arg period expects weeks
    eg 2 means 2 * 7 = 14 days.
    """
    end_period = utc_now()
    start_period = datetime(2011, 01, 01)

    if current_streak:
        start_period = user.userprofile.current_streak_start
        end_period = user.userprofile.current_streak_end
        if utc_now().date() - end_period > timedelta(days=1):
            return 0
    elif longest_streak:
        start_period = user.userprofile.longest_streak_start
        end_period = user.userprofile.longest_streak_end
    elif period > 0:
            start_period = utc_now().date() - timedelta(days=(period * 7))

    query = user.ng_reports.filter(report_date__range=(start_period,
                                                       end_period))

    return query.count()
