# This is your project's main settings file that can be committed to your
# repo. If you need to override a setting locally, use settings_local.py
import logging
import os

from django.utils.functional import lazy
from django_jinja.builtins import DEFAULT_EXTENSIONS
from django_sha2 import get_password_hashers

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
path = lambda *a: os.path.abspath(os.path.join(ROOT, *a))  # noqa
# Defines the views served for root URLs.
ROOT_URLCONF = 'remo.urls'
DEV = False
DEBUG = False

# Application definition
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    'django_jinja',
    'django_browserid',
    'tastypie',
    'waffle',
    'import_export',
    'django_nose',
    'django_filters',
    'rest_framework',
    'session_csrf',
    'compressor',
    'product_details',
    'djcelery',
    # Project specific apps
    'remo.base',
    'remo.profiles',
    'remo.featuredrep',
    'remo.dashboard',
    'remo.remozilla',
    'remo.reports',
    'remo.api',
    'remo.events',
    'remo.voting',
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'session_csrf.CsrfMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
    'remo.base.middleware.RegisterMiddleware',
    'waffle.middleware.WaffleMiddleware'
)

# Media and static files settings
STATIC_ROOT = path('static')
STATIC_URL = '/static/'

# Storage of static files
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_CSS_FILTERS = (
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter'
)
COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
# Absolute path to the directory that holds media.
MEDIA_ROOT = path('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
MEDIA_URL = '/media/'

SESSION_COOKIE_SECURE = not DEBUG

# Instruct session-csrf to always produce tokens for anonymous users
ANON_ALWAYS = True

FROM_EMAIL = 'The ReMoBot <reps@mozilla.com>'

ADMINS = (
    ('Mozilla Reps Devs', 'reps-dev@mozilla.com'),
)

MANAGERS = ADMINS

ETHERPAD_URL = 'https://public.etherpad-mozilla.org/p/'
ETHERPAD_PREFIX = 'remo-'

CONTRIBUTE_URL = ('http://www.mozilla.org/contribute/'
                  'event/?callbackurl=%(callbackurl)s')


REPS_MENTORS_LIST = 'reps-mentors@lists.mozilla.org'
REPS_COUNCIL_ALIAS = 'reps-council@mozilla.com'

# Mozillians API
MOZILLIANS_API_BASE = 'https://mozillians.org'

ALLOWED_HOSTS = ['reps.mozilla.org']

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
# Statsd Graphite
STATSD_CLIENT = 'django_statsd.clients.normal'
MAPBOX_TOKEN = 'examples.map-i86nkdio'

SERVER_EMAIL = 'reps-dev@mozilla.com'

CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'session_csrf.context_processor',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.template.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'remo.base.context_processors.globals',
)

TEMPLATES = [
    {
        'BACKEND': 'django_jinja.backend.Jinja2',
        'NAME': 'jinja2',
        'APP_DIRS': True,
        'OPTIONS': {
            'match_extension': '.jinja',
            'newstyle_gettext': True,
            'context_processors': CONTEXT_PROCESSORS,
            'undefined': 'jinja2.Undefined',
            'extensions': DEFAULT_EXTENSIONS + [
                'compressor.contrib.jinja2ext.CompressorExtension',
                'waffle.jinja.WaffleExtension',
                'caching.ext.cache'
            ],
            'globals': {
                'browserid_info': 'django_browserid.helpers.browserid_info',
                'browserid_login': 'django_browserid.helpers.browserid_login',
                'browserid_logout': 'django_browserid.helpers.browserid_logout',
                'browserid_js': 'django_browserid.helpers.browserid_js'
            }
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            'remo/profiles/templates',
        ],
        'OPTIONS': {
            'context_processors': CONTEXT_PROCESSORS
        }
    },
]


def COMPRESS_JINJA2_GET_ENVIRONMENT():
    from django.template import engines
    return engines['jinja2'].env

# Auth
# The first hasher in this list will be used for new passwords.
# Any other hasher in the list can be used for existing passwords.
# Playdoh ships with Bcrypt+HMAC by default because it's the most secure.
# To use bcrypt, fill in a secret HMAC key in your local settings.
BASE_PASSWORD_HASHERS = (
    'django_sha2.hashers.BcryptHMACCombinedPasswordVerifier',
    'django_sha2.hashers.SHA512PasswordHasher',
    'django_sha2.hashers.SHA256PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
)

HMAC_KEYS = {
    '2015-12-15': 'pancakes',
}

PASSWORD_HASHERS = get_password_hashers(BASE_PASSWORD_HASHERS, HMAC_KEYS)

AUTHENTICATION_BACKENDS = [
    'django_browserid.auth.BrowserIDBackend',
    'django.contrib.auth.backends.ModelBackend'
]
# Django-CSP
CSP_DEFAULT_SRC = (
    "'self'",
    'https://*.mozilla.org',
    'http://*.mapbox.com',
    'https://*.mapbox.com',
    'https://*.persona.org',
)
CSP_FONT_SRC = (
    "'self'",
    'http://*.mozilla.net',
    'https://*.mozilla.net',
    'http://*.mozilla.org',
    'https://*.mozilla.org',
    'https://mozorg.cdn.mozilla.net',
    'http://mozorg.cdn.mozilla.net',
)
CSP_IMG_SRC = (
    "'self'",
    'data:',
    'http://*.mozilla.net',
    'https://*.mozilla.net',
    'http://*.mozilla.org',
    'https://*.mozilla.org',
    '*.google-analytics.com',
    '*.gravatar.com',
    '*.wp.com',
    'https://*.libravatar.org',
    'http://*.mapbox.com',
    'https://*.mapbox.com',
)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-eval'",  # TODO: remove this by pre-compiling handlebars
    'http://www.mozilla.org',
    'https://www.mozilla.org',
    'http://*.mozilla.net',
    'https://*.mozilla.net',
    'https://*.google-analytics.com',
    'https://login.persona.org',
    'http://*.mapbox.com',
    'https://*.mapbox.com',
)

CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    'http://www.mozilla.org',
    'https://www.mozilla.org',
    'http://*.mozilla.net',
    'https://*.mozilla.net',
    'http://*.mapbox.com',
    'https://*.mapbox.com',
)

CSP_CHILD_SRC = (
    "'self'",
    'https://login.persona.org',
)

LOG_LEVEL = logging.INFO
HAS_SYSLOG = True
LOGGING_CONFIG = None

SYSLOG_TAG = 'http_app_remo'
LOGGING = {
    'loggers': {
        'remo': {'level': logging.INFO}
    }
}

# Add BrowserID as authentication backend
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',
                           'remo.base.backend.RemoBrowserIDBackend')


# Required for BrowserID. Very important security feature
SITE_URL = 'https://reps.mozilla.org'

# Override BrowserID verification
BROWSERID_VERIFY_CLASS = 'remo.base.views.BrowserIDVerify'
# Browserid Audiences
BROWSERID_AUDIENCES = [SITE_URL]

# Optional BrowserID settings
LOGIN_REDIRECT_URL = '/dashboard/'
LOGIN_REDIRECT_URL_FAILURE = '/'
LOGOUT_REDIRECT_URL = '/'

# This is needed to get a CRSF token in /admin
ANON_ALWAYS = True

FROM_EMAIL = 'The ReMoBot <reps@mozilla.com>'

ADMINS = (
    ('Mozilla Reps Devs', 'reps-dev@mozilla.com'),
)
MANAGERS = ADMINS

# Allow robots to crawl the site.
ENGAGE_ROBOTS = True

TIME_ZONE = 'UTC'
USE_TZ = True

ETHERPAD_URL = 'https://public.etherpad-mozilla.org/p/'
ETHERPAD_PREFIX = 'remo-'

CONTRIBUTE_URL = ('http://www.mozilla.org/contribute/'
                  'event/?callbackurl=%(callbackurl)s')


REPS_MENTORS_LIST = 'reps-mentors@lists.mozilla.org'
REPS_COUNCIL_ALIAS = 'reps-council@mozilla.com'

# Mozillians API
MOZILLIANS_API_BASE = 'https://mozillians.org'

ALLOWED_HOSTS = ['reps.mozilla.org']

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_RESULTS_EXPIRES = 3600
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_RESULT_BACKEND = 'amqp'
CELERY_ALWAYS_EAGER = True

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True


def _request_args():
    from django.conf import settings
    from django.utils.translation import ugettext_lazy as _lazy

    args = {'siteName': _lazy('Mozilla Reps'), }

    if settings.SITE_URL.startswith('https'):
        args['siteLogo'] = '/static/base/img/remo/remo_logo_medium.png'

    return args
BROWSERID_REQUEST_ARGS = lazy(_request_args, dict)()

# Statsd Graphite
STATSD_CLIENT = 'django_statsd.clients.normal'

# Paginator settings
ITEMS_PER_PAGE = 20

# django-celery setup
import djcelery  # noqa
djcelery.setup_loader()

MAPBOX_TOKEN = 'examples.map-i86nkdio'

SERVER_EMAIL = 'reps-dev@mozilla.com'

# Django Rest Framework
REST_FRAMEWORK = {
    'URL_FIELD_NAME': '_url',
    'PAGINATE_BY': 20,
    'MAX_PAGINATE_BY': 100,
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ),
    'DATE_FORMAT': None,
    'TIME_FORMAT': None,
    'DATETIME_FORMAT': None,
}

# URL constants
LIBRAVATAR_URL = 'https://seccdn.libravatar.org/avatar/'

# Django-Cache-Machine
CACHE_INVALIDATE_ON_CREATE = 'whole-model'

# Auth
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
