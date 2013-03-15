from jingo import register


@register.filter
def get_users_voted(poll):
    """Returns the number of users voted to the specific poll."""

    return poll.users_voted.all().count()
