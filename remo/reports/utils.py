from datetime import date, datetime

from django.core.urlresolvers import reverse

from remo.base.utils import get_object_or_none, go_back_n_months
from remo.base.utils import go_fwd_n_months, number2month
from remo.reports.models import Report
from remo.reports.helpers import get_mentees, get_report_view_url


def get_reports_for_year(user, start_year, end_year=None,
                         allow_empty=False, private=True):
    """Return a list of reports for year."""
    reports_list = {}
    tmp_date = datetime.today()
    up = user.userprofile
    today = datetime(year=tmp_date.year, month=tmp_date.month, day=1)
    date_joined = up.date_joined_program
    tmp_date = go_fwd_n_months(date_joined)
    month_first_report = datetime(year=tmp_date.year,
                                  day=1, month=tmp_date.month)

    if not end_year:
        end_year = start_year

    for year in range(max(start_year, date_joined.year), end_year+1):
        reports = user.reports.filter(month__year=year)

        reports_list[year] = []

        for month in range(1, 13):
            month_details = {'name': number2month(month, full_name=False),
                             'fullname': number2month(month, full_name=True)}
            if reports.filter(month__month=month).exists():
                report = reports.get(month__month=month)
                month_details['report'] = report
                month_details['class'] = 'exists'
                month_details['link'] = get_report_view_url(report)
            else:
                month_details['report'] = None
                dateobj = datetime(year=year, month=month, day=1)

                if (private or month_first_report > dateobj or
                    dateobj >= today):
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
        dateobj = go_back_n_months(date.today(), first_day=True)

    mentees = get_mentees(user)
    mentees_list = {'month': dateobj.strftime("%B %Y"),
                    'reports': []}

    for mentee in mentees:
        report = get_object_or_none(Report, user=mentee, month=dateobj)
        if report == None:
            status = 'notfilled'
        elif report.overdue:
            status = 'overdue'
        else:
            status = ''

        mentees_list['reports'].append({'user': mentee, 'status': status,
                                        'report': report})

    return mentees_list
