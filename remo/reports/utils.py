from datetime import datetime

from django.utils.timezone import now

from remo.base.utils import get_date


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
