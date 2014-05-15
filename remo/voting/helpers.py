from django.db.models import Q
from django.contrib.auth.models import User

from jingo import register


@register.filter
def get_users_voted(poll):
    """Return the number of users voted to the specific poll."""

    return poll.users_voted.all().count()


def get_voters_per_group(poll):
    """Return the number of users of a specific poll per group."""

    return User.objects.filter(groups=poll.valid_groups).count()


@register.filter
def get_meter_value(poll):
    """Return the actual value for the meter element."""

    users_voted = float(get_users_voted(poll))
    voters_group = float(get_voters_per_group(poll))
    try:
        val = (users_voted/voters_group)*100
        return int(val)
    except ZeroDivisionError:
        return 0


@register.function
def user_has_poll_permissions(user, poll):
    """Check if a user's group has permissions for a specific poll."""

    if user.groups.filter(Q(id=poll.valid_groups.id) |
                          Q(name='Admin')).exists():
        return True
    return False
