from django.contrib.auth.models import User
from django.contrib.markup.templatetags import markup
from jingo import register
from jinja2 import Markup


@register.filter
def restructuredtext(text):
    """Return text rendered as RestructuredText."""
    return Markup(markup.restructuredtext(text))


@register.filter
def get_display_name(obj):
    """Return obj display_name if obj is User. Otherwise return None."""
    if isinstance(obj, User):
        return obj.userprofile.display_name


@register.filter
def format_datetime(obj, type=None):
    """Return datetime obj formatted."""
    if type=="full":
        return obj.strftime("%d %B %Y %H:%M")
    return obj.strftime("%Y-%m-%d %H:%M")
