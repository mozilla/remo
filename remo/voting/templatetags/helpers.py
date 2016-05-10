from django.db.models import Q
from django.contrib.auth.models import User

from django_jinja import library

from remo.base.utils import get_object_or_none
from remo.voting.models import Vote


@library.filter
def get_users_voted(poll):
    """Return the number of users voted to the specific poll."""

    return poll.users_voted.all().count()


def get_voters_per_group(poll):
    """Return the number of users of a specific poll per group."""

    return User.objects.filter(groups=poll.valid_groups).count()


@library.filter
def get_meter_value(poll):
    """Return the actual value for the meter element."""

    users_voted = float(get_users_voted(poll))
    voters_group = float(get_voters_per_group(poll))
    try:
        val = (users_voted / voters_group) * 100
        return int(val)
    except ZeroDivisionError:
        return 0


@library.global_function
def user_has_poll_permissions(user, poll):
    """Check if a user's group has permissions for a specific poll."""

    if user.groups.filter(Q(id=poll.valid_groups.id) |
                          Q(name='Admin')).exists():
        return True
    return False


@library.global_function
def user_has_voted(user, poll):
    if Vote.objects.filter(poll=poll, user=user).exists():
        return True
    return False


@library.global_function
def get_nominee(full_name):
    first_name, last_name = full_name.rsplit(' ', 1)
    q_params = {'first_name': first_name,
                'last_name': last_name,
                'groups__name': 'Rep'}
    user = get_object_or_none(User, **q_params)
    if not user:
        q_params['first_name'], q_params['last_name'] = full_name.split(' ', 1)
    return get_object_or_none(User, **q_params)
