from django.conf import settings
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


@register.function
def get_static_map_url(width, height, lon, lat, zoom=4):
    api_key = settings.CLOUDMADE_API
    marker_id = settings.CLOUDMADE_MARKER_PURPLE
    URL = ('http://staticmaps.cloudmade.com/%(api_key)s/staticmap?'
           'size=%(width)sx%(height)s&center=%(lon)s,%(lat)s&zoom=%(zoom)s'
           '&marker=id:%(marker_id)s|%(lon)s,%(lat)s')
    return URL % {'api_key': api_key, 'width': width, 'height': height,
                  'marker_id': marker_id, 'lat': lat, 'lon': lon,
                  'zoom': zoom}
