from math import ceil
from django.utils.timezone import now as utc_now

from jingo import register


@register.function
def count_ng_reports(obj, current_streak=False, longest_streak=False,
                     period=0):
    # Avoid circular dependencies
    import utils
    return utils.count_user_ng_reports(obj, current_streak,
                                       longest_streak, period)


@register.function
def is_same_day(first_date, second_date=None):
    if first_date == (second_date or utc_now().date()):
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
