import base64
import binascii

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.markup.templatetags import markup
from jingo import register
from jinja2 import Markup

from Crypto.Cipher import AES

AES_PADDING = 16
AES_IV_LENGTH = 16


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
    """Return static map url."""
    api_key = settings.CLOUDMADE_API
    marker_id = settings.CLOUDMADE_MARKER_85
    URL = ('http://staticmaps.cloudmade.com/%(api_key)s/staticmap?'
           'styleid=997&size=%(width)sx%(height)s&center=%(lon)s,%(lat)s'
           '&zoom=%(zoom)s&marker=id:%(marker_id)s|%(lon)s,%(lat)s')
    return URL % {'api_key': api_key, 'width': width, 'height': height,
                  'marker_id': marker_id, 'lat': lat, 'lon': lon,
                  'zoom': zoom}


def pad_string(str, block_size):
    """Pad string to reach block_size."""
    numpad = block_size - (len(str) % block_size)
    return str + numpad * chr(numpad)


def enc_string(str):
    """Return AES CBC encrypted string."""
    key = binascii.unhexlify(settings.MAILHIDE_PRIV_KEY)
    mode = AES.MODE_CBC
    iv = '\000' * AES_IV_LENGTH
    obj = AES.new(key, mode, iv)
    return obj.encrypt(str)


@register.filter
def mailhide(value):
    """Return MailHided email address.

    Code from https://code.google.com/p/django-mailhide-filter
    """
    args = {}
    padded_value = pad_string(value, AES_PADDING)
    encrypted_value = enc_string(padded_value)

    args['public_key'] = settings.MAILHIDE_PUB_KEY
    args['encrypted_email'] = base64.urlsafe_b64encode(encrypted_value)
    args['domain'] = value[value.index('@')+1:]
    args['email'] = value[0]

    result = ("""<a href="http://mailhide.recaptcha.net/d?k=%(public_key)s&"""
              """c=%(encrypted_email)s" onclick="window.open('"""
              """http://mailhide.recaptcha.net/d?k=%(public_key)s&"""
              """c=%(encrypted_email)s', '', 'toolbar=0,scrollbars=0,"""
              """location=0,statusbar=0,menubar=0,resizable=0,width=500,"""
              """height=300'); return false;" title="Reveal this e-mail"""
              """ address">%(email)s...@%(domain)s</a>""") % args

    return Markup(result)
