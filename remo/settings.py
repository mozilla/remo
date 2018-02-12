import json
import logging

from decouple import config
from dj_database_url import parse as db_url
from django_jinja.builtins import DEFAULT_EXTENSIONS
from django_sha2 import get_password_hashers
from unipath import Path

# Root path of the project
ROOT = Path(__file__).parent.parent
# Defines the views served for root URLs.
ROOT_URLCONF = 'remo.urls'
STATIC_ROOT = Path('static').resolve()
# Absolute path to the directory that holds media.
MEDIA_ROOT = Path('media').resolve()


# Application definition
########################
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
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'session_csrf.CsrfMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
    'remo.base.middleware.RegisterMiddleware',
    'waffle.middleware.WaffleMiddleware',
)

#############################
# ReMo database configuration
#############################

DATABASES = {
    'default': config('DATABASE_URL', cast=db_url)
}

############################
# ReMo environment variables
############################
DEBUG = config('DEBUG', default=False, cast=bool)
DEV = config('DEV', default=False, cast=bool)

# Media and static files settings
STATIC_URL = config('STATIC_URL', default='/static/')

# URL that handles the media served from MEDIA_ROOT.
MEDIA_URL = config('MEDIA_URL', default='/media/')

# Session/Cookie settings
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = config('SESSION_COOKIE_HTTPONLY', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)

# Instruct session-csrf to always produce tokens for anonymous users
# This is needed to get a CRSF token in /admin
ANON_ALWAYS = config('ANON_ALWAYS', default=True, cast=bool)

# Django Security Middleware
SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Project emails
REPS_MENTORS_LIST = config('REPS_MENTORS_LIST', default='reps-mentors@lists.mozilla.org')
REPS_COUNCIL_ALIAS = config('REPS_COUNCIL_ALIAS', default='reps-council@mozilla.com')
REPS_REVIEW_ALIAS = config('REPS_REVIEW_ALIAS', default='reps-review@mozilla.com')
FROM_EMAIL = config('FROM_EMAIL', default='The ReMoBot <reps@mozilla.com>')
SERVER_EMAIL = config('SERVER_EMAIL', default='reps-dev@mozilla.com')
ADMINS = (
    ('Mozilla Reps Devs', SERVER_EMAIL),
)
MANAGERS = ADMINS

# SMTP settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django_ses.SESBackend')
if EMAIL_BACKEND == 'django_ses.SESBackend':
    if config('AWS_SES_OVERRIDE_BOTO', default=False, cast=bool):
        AWS_SES_ACCESS_KEY_ID = config('AWS_SES_ACCESS_KEY_ID')
        AWS_SES_SECRET_ACCESS_KEY = config('AWS_SES_SECRET_ACCESS_KEY')
    AWS_SES_REGION_NAME = config('AWS_SES_REGION_NAME',
                                 default='us-east-1')
    AWS_SES_REGION_ENDPOINT = config('AWS_SES_REGION_ENDPOINT',
                                     default='email.us-east-1.amazonaws.com')
else:
    EMAIL_HOST = config('SMTP_EMAIL_HOST', default='localhost')
    EMAIL_PORT = config('SMTP_EMAIL_PORT', default='1025')
    EMAIL_HOST_USER = config('SMTP_EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('SMTP_EMAIL_HOST_PASSWORD', default='')
    EMAIL_USE_TLS = config('SMTP_EMAIL_USE_TLS', default=False, cast=bool)

# Etherpad
ETHERPAD_URL = config('ETHERPAD_URL', default='https://public.etherpad-mozilla.org/p/')
ETHERPAD_PREFIX = config('ETHERPAD_PREFIX', default='remo-')

# Mozillians API
MOZILLIANS_API_URL = config('MOZILLIANS_API_URL', default='')
MOZILLIANS_API_KEY = config('MOZILLIANS_API_KEY', default='')

# mozillians.org url
MOZILLIANS_ORG = config('MOZILLIANS_ORG', default='https://mozillians.org')

# Project secutity settings
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])
SECRET_KEY = config('SECRET_KEY')
HMAC_KEYS = {
    '2015-12-15': 'pancakes',
}
SITE_URL = config('SITE_URL', default='https://reps.mozilla.org')

# CSP configuration
CSP_REPORT_ONLY = config('CSP_REPORT_ONLY', default=False, cast=bool)
CSP_REPORT_ENABLE = config('CSP_REPORT_ENABLE', default=True, cast=bool)
CSP_REPORT_URI = config('CSP_REPORT_URI', default='/capture-csp-violation')

# Celery configuration
CELERY_ENABLE_UTC = config('CELERY_ENABLE_UTC', default=True, cast=bool)
CELERY_TIMEZONE = config('CELERY_TIMEZONE', default='UTC')
CELERY_TASK_RESULT_EXPIRES = config('CELERY_TASK_RESULT_EXPIRES', default=3600, cast=int)
CELERY_ACCEPT_CONTENT = ['pickle', 'json']
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://broker:6379/1')
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)
CELERY_TASK_SERIALIZER = config('CELERY_TASK_SERIALIZER', default='pickle')
REDIS_CONNECT_RETRY = config('REDIS_CONNECT_RETRY',
                             default=CELERY_RESULT_BACKEND == 'redis', cast=bool)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://broker:6379/1')
if CELERY_BROKER_URL.startswith('redis'):
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'visibility_timeout': config('REDIS_VISIBILITY_TIMEOUT', default=604800, cast=int)
    }

# Mapbox
MAPBOX_TOKEN = config('MAPBOX_TOKEN', default='')

# Gravatar
LIBRAVATAR_URL = config('LIBRAVATAR_URL', default='https://seccdn.libravatar.org/avatar/')

# Planet
PLANET_URL = config('PLANET_URL', default='http://planet.mozillareps.org/rss20.xml')
PLANET_MAX_TIMEOUT = config('PLANET_MAX_TIMEOUT', default=5, cast=int)

# Bugzilla
REMOZILLA_USERNAME = config('REMOZILLA_USERNAME', default='')
REMOZILLA_PASSWORD = config('REMOZILLA_PASSWORD', default='')
REMOZILLA_API_KEY = config('REMOZILLA_API_KEY', default='')

# Mailhide
MAILHIDE_PUB_KEY = config('MAILHIDE_PUB_KEY', default='')
MAILHIDE_PRIV_KEY = config('MAILHIDE_PRIV_KEY', default='')

# OIDC settings
OIDC_CALLBACK_CLASS = config('OIDC_CALLBACK_CLASS', default='remo.base.views.OIDCCallbackView')
OIDC_STORE_ACCESS_TOKEN = config('OIDC_STORE_ACCESS_TOKEN', default=True, cast=bool)
OIDC_RP_CLIENT_SECRET_ENCODED = config('OIDC_RP_CLIENT_SECRET_ENCODED', default=True, cast=bool)
AUTH0_DOMAIN = config('AUTH0_DOMAIN', default='')
AUTH0_CLIENT_ID = config('AUTH0_CLIENT_ID', default='')
OIDC_OP_AUTHORIZATION_ENDPOINT = config('OIDC_OP_AUTHORIZATION_ENDPOINT', default='')
OIDC_OP_TOKEN_ENDPOINT = config('OIDC_OP_TOKEN_ENDPOINT', default='')
OIDC_OP_USER_ENDPOINT = config('OIDC_OP_USER_ENDPOINT', default='')
OIDC_RP_CLIENT_ID = config('OIDC_RP_CLIENT_ID', default='')
OIDC_RP_CLIENT_SECRET = config('OIDC_RP_CLIENT_SECRET', default='')
OIDC_OP_DOMAIN = config('OIDC_OP_DOMAIN', default='auth.mozilla.auth0.com')
LOGIN_REDIRECT_URL = config('LOGIN_REDIRECT_URL', default='/dashboard/')
LOGIN_REDIRECT_URL_FAILURE = config('LOGIN_REDIRECT_URL_FAILURE', default='/')
LOGOUT_REDIRECT_URL = config('LOGOUT_REDIRECT_URL', default='/')

# Allow robots to crawl the site.
ENGAGE_ROBOTS = config('ENGAGE_ROBOTS', default=True, cast=bool)

# Django timezone
TIME_ZONE = config('TIME_ZONE', default='UTC')
USE_TZ = config('USE_UTC', default=True)

# Django compressor
COMPRESS_ENABLED = config('COMPRESS_ENABLED', default=True, cast=bool)
COMPRESS_OFFLINE = config('COMPRESS_OFFLINE', default=True, cast=bool)

# Paginator settings
ITEMS_PER_PAGE = config('ITEMS_PER_PAGE', default=20, cast=int)

# Syslog
HAS_SYSLOG = config('HAS_SYSLOG', default=True, cast=bool)

###################
# App Configuration
###################
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
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Statsd Graphite
STATSD_CLIENT = 'django_statsd.clients.normal'

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
                'waffle.jinja.WaffleExtension'
            ],
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            Path('remo/profiles/templates').resolve(),
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
    'data:',
    'https://www.mozilla.org',
    'https://*.mozilla.net',
    'https://ssl.google-analytics.com',
    'https://*.mapbox.com',
    'https://ajax.googleapis.com',
    'https://search.twitter.com',
    'https://secure.flickr.com',

    # Allow google-analytics
    "'sha256-8w+7qKYFP3Pxpf/bGVp4hbU7I3vcqFSwUaUnkuBl4mc='",
    # Allow Django admin scripts
    "'sha256-YAeNgc46QF0YbTBOhlJJtwaOwJTu1UEvFVe3ljLBobg='",
    "'sha256-oCFnYcAHSMaBkeLUfc1dt043IHsvnM7FYC8rNVTr4z4='",
    "'sha256-SjfMQo173oGUAkxAJmT3YNTlryI5ou9f6HkUz0QUJQs='",
    "'sha256-lV6Q4R6n6P5zkatU4DiQ40kagqmlwvF0XXvRV/UfpPU='",
    "'sha256-fH3rM69L3MlQuLHwmENXZ9SSP9u+7mECRGOpE5pY/Hw='",
    "'sha256-fH3rM69L3MlQuLHwmENXZ9SSP9u+7mECRGOpE5pY/Hw='",
    "'sha256-aGve+DiECXZoKccqA0Ry5ralTx6/zA1ehcFkWyKrlrU='",
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

# Logging
LOGGING_CONFIG = None
LOG_LEVEL = logging.INFO
SYSLOG_TAG = 'http_app_remo'
RAVEN_CONFIG = config('RAVEN_CONFIG', cast=json.loads, default='{}')

LOGGING = {
    'loggers': {
        'remo': {'level': LOG_LEVEL}
    }
}

HEALTHCHECKS_IO_URL = config('HEALTHCHECKS_IO_URL', default='')

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

# Cache
CACHES = {
    'default': {
        'BACKEND': config('CACHE_BACKEND',
                          default='django.core.cache.backends.memcached.MemcachedCache'),
        'LOCATION': config('CACHE_URL', default='127.0.0.1:11211'),
        'KEY_PREFIX': config('CACHE_KEY_PREFIX', default='remo')
    }
}

if DEV:
    CSP_DEFAULT_SRC += (
        'http://*.mapbox.com',
    )
    CSP_FONT_SRC += (
        'http://*.mozilla.net',
        'http://*.mozilla.org',
    )
    CSP_IMG_SRC += (
        'http://*.mozilla.net',
        'http://*.mozilla.org',
        'http://*.mapbox.com',
    )
    CSP_SCRIPT_SRC += (
        'http://*.mozilla.net',
        'http://*.mozilla.org',
        'http://*.mapbox.com',
    )
    CSP_STYLE_SRC += (
        'http://*.mozilla.net',
        'http://*.mozilla.org',
        'http://*.mapbox.com',
    )

if DEBUG:
    for backend in TEMPLATES:
        backend['OPTIONS']['debug'] = DEBUG
