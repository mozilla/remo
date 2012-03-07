from django.contrib.auth.models import User
from django.contrib.markup.templatetags import markup
from jingo import register


@register.filter
def restructuredtext(text):
    return markup.restructuredtext(text)


@register.filter
def get_display_name(obj):
    """Return obj display_name if obj is User. Otherwise return None."""
    if isinstance(obj, User):
        return obj.userprofile.display_name
