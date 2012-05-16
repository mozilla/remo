from datetime import date, datetime

from django.core.urlresolvers import reverse

from remo.base.utils import get_object_or_none, go_back_n_months
from remo.base.utils import go_fwd_n_months, number2month
from remo.reports.models import Report
from remo.reports.helpers import get_mentees, get_report_view_url

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

    for year in range(max(start_year, date_joined.year), end_year+1):
        reports = user.reports.filter(month__year=year)

        reports_list[year] = []

        for month in range(1, 13):
            month = datetime(year=year, month=month, day=1)
            month_details = {'name': number2month(month.month,
                                                  full_name=False),
                             'fullname': number2month(month.month,
                                                      full_name=True)}
            if (reports.filter(month=month).exists() and
                ((permission > 1 and month == today) or (month < today))):
                report = reports.get(month=month)
                month_details['report'] = report
                month_details['class'] = 'exists'
                month_details['link'] = get_report_view_url(report)
            else:
                month_details['report'] = None

                if (permission < 3 or month_first_report > month or
                    month > today):
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
