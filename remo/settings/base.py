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
    'raven.contrib.django.raven_compat',
    'mozilla_django_oidc',
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
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'remo.base.middleware.RegisterMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'mozilla_django_oidc.contrib.auth0.middleware.RefreshIDToken',
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
# This is needed to get a CRSF token in /admin
ANON_ALWAYS = True

# Security Middleware
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000  # 1 year

FROM_EMAIL = 'The ReMoBot <reps@mozilla.com>'

ADMINS = (
    ('Mozilla Reps Devs', 'reps-dev@mozilla.com'),
)

MANAGERS = ADMINS

ETHERPAD_URL = 'https://public.etherpad-mozilla.org/p/'
ETHERPAD_PREFIX = 'remo-'

REPS_MENTORS_LIST = 'reps-mentors@lists.mozilla.org'
REPS_COUNCIL_ALIAS = 'reps-council@mozilla.com'
REPS_REVIEW_ALIAS = 'reps-review@mozilla.com'

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
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            path('remo/profiles/templates'),
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
    'remo.base.backend.RemoAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend'
]
# Django-CSP
CSP_DEFAULT_SRC = (
    "'self'",
    'https://*.mozilla.org',
    'https://*.mapbox.com',
)

CSP_FONT_SRC = (
    "'self'",
    'https://*.mozilla.net',
    'https://*.mozilla.org',
    'https://mozorg.cdn.mozilla.net',
)

CSP_IMG_SRC = (
    "'self'",
    'data:',
    'https://*.mozilla.net',
    'https://*.mozilla.org',
    '*.google-analytics.com',
    '*.gravatar.com',
    '*.wp.com',
    'https://*.libravatar.org',
    'https://*.mapbox.com',
    'https://*.staticflickr.com',
)

CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-eval'",  # TODO: remove this by pre-compiling handlebars
    'https://www.mozilla.org',
    'https://*.mozilla.net',
    'https://ssl.google-analytics.com',
    'https://*.mapbox.com',
    'https://ajax.googleapis.com',
    'https://search.twitter.com',
    'https://secure.flickr.com',

    # Allow google-analytics
    "'sha256-8w+7qKYFP3Pxpf/bGVp4hbU7I3vcqFSwUaUnkuBl4mc='",
)

CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    'https://www.mozilla.org',
    'https://*.mozilla.net',
    'https://*.mapbox.com',
)

CSP_CHILD_SRC = (
    "'self'",
)

CSP_REPORT_ONLY = False
CSP_REPORT_ENABLE = True
CSP_REPORT_URI = '/capture-csp-violation'

LOG_LEVEL = logging.INFO
HAS_SYSLOG = True
LOGGING_CONFIG = None

SYSLOG_TAG = 'http_app_remo'
LOGGING = {
    'loggers': {
        'remo': {'level': logging.INFO}
    }
}

SITE_URL = 'https://reps.mozilla.org'

LOGIN_REDIRECT_URL = '/dashboard/'
LOGIN_REDIRECT_URL_FAILURE = '/'
LOGOUT_REDIRECT_URL = '/'

# Allow robots to crawl the site.
ENGAGE_ROBOTS = True

TIME_ZONE = 'UTC'
USE_TZ = True

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

# Planet feed URL
PLANET_URL = 'http://planet.mozillareps.org/rss20.xml'

# Django-Cache-Machine
CACHE_INVALIDATE_ON_CREATE = 'whole-model'

# Auth
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}


# Auth0 configuration
def lazy_oidc_op_domain():
    from django.conf import settings

    if settings.SITE_URL == 'https://reps-dev.allizom.org':
        return 'auth-dev.mozilla.auth0.com'
    return 'auth.mozilla.auth0.com'


OIDC_CALLBACK_CLASS = 'remo.base.views.OIDCCallbackView'
OIDC_OP_DOMAIN = lazy(lazy_oidc_op_domain, str)()
OIDC_STORE_ACCESS_TOKEN = True
OIDC_RP_CLIENT_SECRET_ENCODED = True
