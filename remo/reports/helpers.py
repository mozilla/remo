from math import ceil
from django.core.urlresolvers import reverse
from django.utils.timezone import now as utc_now

from jingo import register

from remo.base.utils import number2month


@register.filter
def get_report_edit_url(obj):
    """Return report edit link."""
    up = obj.user.userprofile
    return reverse('reports_edit_report',
                   kwargs={'display_name': up.display_name,
                           'year': obj.month.year,
                           'month': obj.month.strftime('%B')})


@register.filter
def get_report_view_url(obj):
    """Return report view link."""
    up = obj.user.userprofile
    return reverse('reports_view_report',
                   kwargs={'display_name': up.display_name,
                           'year': obj.month.year,
                           'month': obj.month.strftime('%B')})


@register.filter
def get_comment_delete_url(obj):
    """Return the delete url of a comment."""
    up = obj.report.user.userprofile
    month_name = number2month(obj.report.month.month)
    return reverse('reports_delete_report_comment',
                   kwargs={'display_name': up.display_name,
                           'year': obj.report.month.year,
                           'month': month_name,
                           'comment_id': obj.id})


@register.filter
def get_mentees(user):
    return [mentee_profile.user for mentee_profile in
            user.mentees.exclude(registration_complete=False)
                        .order_by('user__last_name', 'user__first_name')]


@register.function
def count_ng_reports(obj, current_streak=False, longest_streak=False,
                     period=0):
    # Avoid circular dependencies
    import utils
    return utils.count_user_ng_reports(obj, current_streak,
                                       longest_streak, period)


@register.filter
def is_date_today(date):
    if date == utc_now().date():
        return True
    return False


@register.function
def date_to_weeks(end_date, start_date=None):
    """Given a past date, return the number of
    weeks passed compared to today.
    """
    if not start_date:
        start_date = utc_now().date()
    number_of_weeks = ceil(float((start_date - end_date).days) / float(7))
    return int(number_of_weeks) or 1
