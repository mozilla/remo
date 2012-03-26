import datetime


def latest_object_or_none(model_class, field_name=None):
    """Identical to Model.latest, except instead of throwing exceptions,
    this returns None.

    """
    try:
        return model_class.objects.latest(field_name)
    except (model_class.DoesNotExist, model_class.MultipleObjectsReturned):
        return None


def get_object_or_none(model_class, **kwargs):
    """Identical to get_object_or_404, except instead of returning Http404,
    this returns None.

    """
    try:
        return model_class.objects.get(**kwargs)
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


def get_or_create_instance(model_class, **kwargs):
    try:
        return model_class.objects.get(**kwargs), False
    except model_class.DoesNotExist:
        return model_class(**kwargs), True
