import base64
import binascii
import re
import time
import urllib
import urlparse
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.urlresolvers import reverse
from django.template import defaultfilters
from django.template.loader import render_to_string
from django.utils.encoding import smart_str
from django.utils.html import strip_tags

import jinja2
from Crypto.Cipher import AES
from jingo import register
from product_details import product_details

from remo.base import utils


AES_PADDING = 16
AES_IV_LENGTH = 16
LINE_LIMIT = 75
FOLD_SEP = u'\r\n '

COUNTRIES_NAME_TO_CODE = {}
for code, name in product_details.get_regions('en').items():
    name = name.lower()
    COUNTRIES_NAME_TO_CODE[name] = code


# Yanking filters from Django.
register.filter(strip_tags)
register.filter(defaultfilters.timesince)
register.filter(defaultfilters.truncatewords)


@register.function
def thisyear():
    """The current year."""
    return jinja2.Markup(datetime.date.today().year)


@register.function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates."""
    return reverse(viewname, args=args, kwargs=kwargs)


@register.filter
def urlparams(url_, hash=None, **query):
    """Add a fragment and/or query paramaters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url.fragment

    # Use dict(parse_qsl) so we don't get lists of values.
    q = url.query
    query_dict = dict(urlparse.parse_qsl(smart_str(q))) if q else {}
    query_dict.update((k, v) for k, v in query.items())

    query_string = _urlencode([(k, v) for k, v in query_dict.items()
                               if v is not None])
    new = urlparse.ParseResult(url.scheme, url.netloc, url.path, url.params,
                               query_string, fragment)
    return new.geturl()


def _urlencode(items):
    """A Unicode-safe URLencoder."""
    try:
        return urllib.urlencode(items)
    except UnicodeEncodeError:
        return urllib.urlencode([(k, smart_str(v)) for k, v in items])


@register.filter
def urlencode(txt):
    """Url encode a path."""
    if isinstance(txt, unicode):
        txt = txt.encode('utf-8')
    return urllib.quote_plus(txt)


@register.function
def static(path):
    return staticfiles_storage.url(path)


@register.filter
def markdown(text):
    """Return text rendered as Markdown."""
    return jinja2.Markup(markdown(text, 'safe'))


@register.filter
def get_display_name(obj):
    """Return obj display_name if obj is User. Otherwise return None."""
    if isinstance(obj, User):
        return obj.userprofile.display_name


@register.filter
def format_datetime(obj, type=None):
    """Return datetime obj formatted."""
    if type == 'full':
        return obj.strftime('%d %B %Y %H:%M')
    return obj.strftime('%Y-%m-%d %H:%M')


@register.filter
def format_datetime_iso(obj):
    """Return datetime obj ISO formatted."""
    return obj.strftime('%Y-%m-%dT%H:%M:%S')


@register.filter
def format_datetime_unix(obj):
    """Return unix representation of obj."""
    return time.mktime(obj.timetuple())


@register.filter
def format_datetime_utc(obj):
    """Return datetime object UTC formatted."""
    return obj.strftime('%Y%m%dT%H%M%S')


@register.filter
def strftime(obj, style):
    """Return string of datetime object formatted with style."""
    return obj.strftime(style)


@register.function
def get_static_map_url(width, height, lon, lat, zoom=4):
    """Return static map url."""
    token = settings.MAPBOX_TOKEN
    base_url = 'https://api.tiles.mapbox.com/v3/%(tok)s/'
    marker_query = 'pin-m(%(lon)s,%(lat)s)/'
    center_query = '%(lon)s,%(lat)s,%(zoom)s/%(width)sx%(height)s.png'

    URL = base_url + marker_query + center_query

    return URL % {'tok': token, 'width': width, 'height': height,
                  'lat': lat, 'lon': lon, 'zoom': zoom}


@register.function
def get_next_url(request):
    """Return next_url stored in session or Dashboard."""
    if 'next_url' in request.session:
        return request.session.pop('next_url')
    elif request.get_full_path() == '/':
        return reverse('dashboard')

    return request.get_full_path()


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
    args['domain'] = value[value.index('@') + 1:]
    args['email'] = value[0]

    result = ("""<a href="http://mailhide.recaptcha.net/d?k=%(public_key)s&"""
              """c=%(encrypted_email)s" onclick="window.open('"""
              """http://mailhide.recaptcha.net/d?k=%(public_key)s&"""
              """c=%(encrypted_email)s', '', 'toolbar=0,scrollbars=0,"""
              """location=0,statusbar=0,menubar=0,resizable=0,width=500,"""
              """height=300'); return false;" title="Reveal this e-mail"""
              """ address">%(email)s...@%(domain)s</a>""") % args

    return jinja2.Markup(result)


@register.filter
def get_bugzilla_url(bug_id):
    """Return bugzilla url for bug_id."""
    return u'https://bugzilla.mozilla.org/show_bug.cgi?id=%d' % bug_id


@register.function
def active(request, pattern):
    """Return 'active-nav' string when pattern matches request's full path."""
    if re.match(pattern, request.get_full_path()):
        return 'active-nav'

    return None


@register.function
def field_with_attrs(bfield, **kwargs):
    """Allows templates to dynamically add html attributes to bound
    fields from django forms.

    Taken from bedrock.
    """
    bfield.field.widget.attrs.update(kwargs)
    return bfield


@register.function
def field_errors(field):
    """Return string with rendered template with field errors."""
    return jinja2.Markup(render_to_string('form-error.html', {'field': field}))


@register.function
def get_full_name(user):
    """Return user's fullname bugzilla style."""
    return u'%s :%s' % (user.get_full_name(), user.userprofile.display_name)


@register.function
def user_is_mozillian(user):
    """Check if a user belongs to Mozillians group."""
    return user.groups.filter(name='Mozillians').exists()


@register.function
def user_is_rep(user):
    """Check if a user belongs to Rep group."""
    return (user.groups.filter(name='Rep').exists() and
            user.userprofile.registration_complete)


@register.function
def user_is_mentor(user):
    """Check if a user belongs to Mentor group."""
    return user.groups.filter(name='Mentor').exists()


@register.function
def user_is_admin(user):
    """Check if a user belongs to Admin group."""
    return user.groups.filter(name='Admin').exists()


@register.function
def user_is_council(user):
    """Check if a user belongs to Council group."""
    return user.groups.filter(name='Council').exists()


@register.function
def user_is_alumni(user):
    """Check if a user belongs to Alumni group."""
    return user.groups.filter(name='Alumni').exists()


@register.filter
def ical_escape_char(text):
    """Escape characters as defined in RFC5545.

    Original code from https://github.com/collective/icalendar
    Altered by John Giannelos <jgiannelos@mozilla.com>

    """

    return (text.replace('\N', '\n')
                .replace('\\', '\\\\')
                .replace(';', r'\;')
                .replace(',', r'\,')
                .replace('\r\n', r'\n')
                .replace('\n', r'\n'))


@register.filter
def ical_format_lines(text):
    """Make a string folded as defined in RFC5545.

    Original code from https://github.com/collective/icalendar
    Altered by John Giannelos <jgiannelos@mozilla.com>

    """

    ret_line = u''
    byte_count = 0
    for char in text:
        char_byte_len = len(char.encode('utf-8'))
        byte_count += char_byte_len
        if byte_count >= LINE_LIMIT:
            ret_line += FOLD_SEP
            byte_count = char_byte_len
        ret_line += char

    return ret_line


@register.function
def get_attr(obj, value, default):
    """Add a gettatr helper in templates."""
    return getattr(obj, value, default)


@register.filter
def absolutify(url):
    """Prepend the SITE_URL to the url."""
    return utils.absolutify(url)


@register.function
def get_date_n_weeks_before(date, weeks=0):
    """Return the date X weeks before date."""
    return date - timedelta(weeks=weeks)


@register.filter
def formset_errors_exist(formset):
    for form in formset.values():
        if form.errors:
            return True
    return False


@register.filter
def get_country_code(country_name):
    """Return country code from country name."""
    return COUNTRIES_NAME_TO_CODE.get(country_name.lower(), '')


@register.filter
def nl2br(string):
    """Turn newlines into <br>."""
    if not string:
        return ''
    return jinja2.Markup('<br>'.join(jinja2.escape(string).splitlines()))


register.filter(defaultfilters.pluralize)
