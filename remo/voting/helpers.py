from jingo import register


@register.filter
def get_users_voted(poll):
    """Return the number of users voted to the specific poll."""

    return poll.users_voted.all().count()


@register.filter
def jinja_linebreaks(text):
    """Replace the newlines \n with <br> tags like
    the django filter 'linebreaks'.

    """
    return text.replace('\n', '<br />')
