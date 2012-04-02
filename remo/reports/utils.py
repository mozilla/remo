import calendar
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse

from remo.base.utils import number2month
from remo.reports.helpers import get_report_view_url


def go_back_n_months(date, n=1):
    """Return date minus n months."""
    tmp_date = datetime(year=date.year, month=date.month, day=15)
    tmp_date -= timedelta(days=31 * n)
    last_day_of_month = calendar.monthrange(tmp_date.year, tmp_date.month)[1]
    return datetime(year=tmp_date.year, month=tmp_date.month,
                    day=min(date.day, last_day_of_month))


def go_fwd_n_months(date, n=1):
    """Return date plus n months."""
    tmp_date = datetime(year=date.year, month=date.month, day=15)
    tmp_date += timedelta(days=31 * n)
    last_day_of_month = calendar.monthrange(tmp_date.year, tmp_date.month)[1]
    return datetime(year=tmp_date.year, month=tmp_date.month,
                    day=min(date.day, last_day_of_month))


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
                date = datetime(year=year, month=month, day=1)

                if (private or month_first_report > date or date >= today):
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
