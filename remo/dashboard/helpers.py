from jingo import register

from remo.profiles.models import UserStatus


@register.filter
def user_is_unavailable(user):
    """Return if a user is unavailable."""
    return UserStatus.objects.filter(user=user, is_unavailable=True).exists()
