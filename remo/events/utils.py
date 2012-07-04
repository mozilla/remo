from models import Event


def get_events_for_user(user, from_date=None, to_date=None):
    """Return events for user from_date to to_date. """
    query = Event.objects.filter(attendees=user)
    if from_date:
        query = query.filter(start__gte=from_date)

    if to_date:
        query = query.filter(start__lt=to_date)

    return query
