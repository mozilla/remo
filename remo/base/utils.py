import calendar
import datetime


def get_object_or_none(model_class, **kwargs):
    """Identical to get_object_or_404, except instead of returning Http404,
    this returns None.

    """
    try:
        return model_class.objects.get(**kwargs)
    except (model_class.DoesNotExist, model_class.MultipleObjectsReturned):
        return None


def get_or_create_instance(model_class, **kwargs):
    """Identical to get_or_create, expect instead of saving the new
    object in the database, this just creates an instance.

    """
    try:
        return model_class.objects.get(**kwargs), False
    except model_class.DoesNotExist:
        return model_class(**kwargs), True


def go_back_n_months(date, n=1, first_day=False):
    """Return date minus n months."""
    if first_day:
        day = 1
    else:
        day = date.day

    tmp_date = datetime.datetime(year=date.year, month=date.month, day=15)
    tmp_date -= datetime.timedelta(days=31 * n)
    last_day_of_month = calendar.monthrange(tmp_date.year, tmp_date.month)[1]
    return datetime.datetime(year=tmp_date.year, month=tmp_date.month,
                             day=min(day, last_day_of_month))


def go_fwd_n_months(date, n=1, first_day=False):
    """Return date plus n months."""
    if first_day:
        day = 1
    else:
        day = date.day

    tmp_date = datetime.datetime(year=date.year, month=date.month, day=15)
    tmp_date += datetime.timedelta(days=31 * n)
    last_day_of_month = calendar.monthrange(tmp_date.year, tmp_date.month)[1]
    return datetime.datetime(year=tmp_date.year, month=tmp_date.month,
                             day=min(day, last_day_of_month))


def latest_object_or_none(model_class, field_name=None):
    """Identical to Model.latest, except instead of throwing exceptions,
    this returns None.

    """
    try:
        return model_class.objects.latest(field_name)
    except (model_class.DoesNotExist, model_class.MultipleObjectsReturned):
        return None


def month2number(month):
    """Convert to month name to number."""
    return datetime.datetime.strptime(month, '%B').month


def number2month(month, full_name=True):
    """Convert to month name to number."""
    if full_name:
        format = '%B'
    else:
        format = '%b'
    return datetime.datetime(year=2000, day=1, month=month).strftime(format)
