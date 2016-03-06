"""
Django settings for the ReMo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import os

from django.utils.functional import lazy

import dj_database_url
from decouple import Csv, config
from django_jinja.builtins import DEFAULT_EXTENSIONS
from django_sha2 import get_password_hashers


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
    'pipeline',
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

for app in config('EXTRA_APPS', default='', cast=Csv()):
    INSTALLED_APPS.append(app)

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
    'waffle.middleware.WaffleMiddleware',
)

ROOT_URLCONF = 'remo.urls'

WSGI_APPLICATION = 'remo.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': config(
        'DATABASE_URL',
        cast=dj_database_url.parse
    )
}


def _request_args():
    from django.conf import settings

    args = {'siteName': u'Mozilla Reps'}

    if settings.SITE_URL.startswith('https'):
        args['siteLogo'] = '/static/base/img/remo/remo_logo_medium.png'

    return args

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ROOT = BASE_DIR

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
HMAC_KEYS = {
    '2015-12-15': config('DJANGO_HMAC_KEY'),
}

LANGUAGE_CODE = config('LANGUAGE_CODE', default='en-us')
TIME_ZONE = config('TIME_ZONE', default='UTC')
USE_I18N = config('USE_I18N', default=False, cast=bool)
USE_L10N = config('USE_L10N', default=False, cast=bool)
USE_TZ = config('USE_TZ', default=True, cast=bool)

# Media and static files settings
STATIC_ROOT = config('STATIC_ROOT', default=os.path.join(BASE_DIR, 'static'))
STATIC_URL = config('STATIC_URL', '/static/')
STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'

MEDIA_ROOT = config('MEDIA_ROOT', default=os.path.join(BASE_DIR, 'media'))
MEDIA_URL = config('MEDIA_URL', '/media/')

SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG,
                               cast=bool)

SITE_URL = config('SITE_URL', default='http://127.0.0.1:8000')
# Paginator settings
ITEMS_PER_PAGE = 20

# Browserid settings
BROWSERID_VERIFY_CLASS = 'remo.base.views.BrowserIDVerify'
BROWSERID_AUDIENCES = config('BROWSERID_AUDIENCES',
                             default='http://127.0.0.1:8000, http://localhost:8000',
                             cast=Csv())
BROWSERID_REQUEST_ARGS = lazy(_request_args, dict)()
LOGIN_REDIRECT_URL = '/dashboard/'
LOGIN_REDIRECT_URL_FAILURE = '/'
LOGOUT_REDIRECT_URL = '/'

# TODO: fix this
LOGGING_CONFIG = None
LOGGING = {}

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
}

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
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'app_dirname': 'jinja2',
            # Don't match loaders based on file extension
            'match_extension': None,
            'newstyle_gettext': True,
            'context_processors': CONTEXT_PROCESSORS,
            'undefined': 'jinja2.Undefined',
            'extensions': DEFAULT_EXTENSIONS + [
                'pipeline.jinja2.PipelineExtension',
                'caching.ext.cache'
            ],
            'globals': {
                'browserid_info': 'django_browserid.helpers.browserid_info',
                'browserid_login': 'django_browserid.helpers.browserid_login',
                'browserid_logout': 'django_browserid.helpers.browserid_logout'
            }
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': CONTEXT_PROCESSORS
        }
    },
]

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
    'django_browserid.auth.BrowserIDBackend',
    'django.contrib.auth.backends.ModelBackend'
]
# Django-CSP
CSP_DEFAULT_SRC = (
    "'self'",
    'https://*.mozilla.org',
)
CSP_FONT_SRC = (
    "'self'",
    'http://*.mozilla.net',
    'https://*.mozilla.net',
    'http://*.mozilla.org',
    'https://*.mozilla.org',
)
CSP_IMG_SRC = (
    "'self'",
    'https://*.gravatar.com',
    'https://*.wp.com',
    'http://*.mozilla.net',
    'https://*.mozilla.net',
    'http://*.mozilla.org',
    'https://*.mozilla.org',
)
CSP_SCRIPT_SRC = (
    "'self'",
    'http://*.mozilla.org',
    'https://*.mozilla.org',
    'http://*.mozilla.net',
    'https://*.mozilla.net',
    'https://login.persona.org',
    'http://*.mapbox.com',
)

CSP_STYLE_SRC = (
    "'self'",
    'http://*.mozilla.org',
    'https://*.mozilla.org',
    'http://*.mozilla.net',
    'https://*.mozilla.net',
)

CSP_CHILD_SRC = (
    "'self'",
    'https://login.persona.org',
)

# This is needed to get a CRSF token in /admin
ANON_ALWAYS = True

# URL constants
GRAVATAR_URL = 'https://seccdn.libravatar.org/avatar/'

# Django-pipeline configuration
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

PIPELINE = {
    'JAVASCRIPT': {
        'base': {
            'source_filenames': (
                'base/js/jquery-1.11.2.js',
                'base/js/modernizr.foundation-4.js',
                'base/js/foundation-4.min.js',
                'base/js/responsive-tables.js',
                'base/js/jquery.prettydate.js',
                'base/js/jquery.imageready.min.js',
                'base/js/placeholder.min.js',
                'base/js/remolib.js',
                'base/js/app.js',
                'base/js/init.js',
                'browserid/api.js',
                'browserid/browserid.js',
            ),
            'output_filename': 'js/base.min.js',
        },
        'mapbox_js': {
            'source_filenames': (
                'base/js/mapbox.js',
                'base/js/L.Control.Locate.js',
                'base/js/map_modal.js',
            ),
            'output_filename': 'js/mapbox_js.min.js',
        },
        'jquery_ui_custom_js': {
            'source_filenames': (
                'events/js/jquery_ui_custom.js',
            ),
            'output_filename': 'js/jquery_ui_custom.min.js',
        },
        'dashboard_reps': {
            'source_filenames': (
                'base/js/stupidtable.js',
                'base/js/dashboard_reps.js',
            ),
            'output_filename': 'js/dashboard_reps.min.js',
        },
        'dashboard_mozillians': {
            'source_filenames': (
                'base/js/stupidtable.js',
                'base/js/dashboard_mozillians.js',
            ),
            'output_filename': 'js/dashboard_mozillians.min.js',
        },
        'dashboard_kpi': {
            'source_filenames': (
                'dashboard/js/d3.min.js',
                'dashboard/js/d3-tip.js',
                'dashboard/js/kpi.js',
            ),
            'output_filename': 'js/dashboard_kpi.min.js',
        },
        'dashboard_action_items': {
            'source_filenames': (
                'dashboard/js/action_items_list.js',
            ),
            'output_filename': 'js/dashboard_action_items_list.min.js',
        },
        'base_content_list': {
            'source_filenames': (
                'base/js/stupidtable.js',
                'base/js/base_content_edit.js',
            ),
            'output_filename': 'js/base_content_list.min.js',
        },
        'rep_availability': {
            'source_filenames': (
                'base/js/edit_availability.js',
            ),
            'output_filename': 'js/rep_availability.min.js',
        },
        'edit_events': {
            'source_filenames': (
                'events/js/events_edit_event.js',
            ),
            'output_filename': 'js/events_edit_event.min.js',
        },
        'list_events': {
            'source_filenames': (
                'base/js/handlebars-v3.0.3.js',
                'events/js/template_helpers.js',
                'base/js/heartcode-canvasloader-min.js',
                'events/js/timeline/timeline.js',
                'events/js/timeline/storyjs-embed.js',
                'events/js/events_list_event.js',
            ),
            'output_filename': 'js/list_events.min.js',
        },
        'view_events': {
            'source_filenames': (
                'events/js/jquery_zflickrfeed.js',
                'events/js/jquery.tweet.js',
                'events/js/events_view_event.js',
            ),
            'output_filename': 'js/view_events.min.js',
        },
        'featuredrep': {
            'source_filenames': (
                'featuredrep/js/featuredrep.js',
            ),
            'output_filename': 'js/featuredrep.min.js',
        },
        'edit_profiles': {
            'source_filenames': (
                'profiles/js/edit_profile.js',
            ),
            'output_filename': 'js/edit_profile.min.js',
        },
        'alumni_profiles': {
            'source_filenames': (
                'profiles/js/alumni_list.js',
            ),
            'output_filename': 'js/alumni_list.min.js',
        },
        'list_profiles': {
            'source_filenames': (
                'base/js/mapbox.js',
                'base/js/L.Control.Locate.js',
                'base/js/handlebars-v3.0.3.js',
                'base/js/heartcode-canvasloader-min.js',
                'profiles/js/profiles_people.js',
            ),
            'output_filename': 'js/list_profiles.min.js',
        },
        'view_profiles': {
            'source_filenames': (
                'profiles/js/profiles_view_profile.js',
            ),
            'output_filename': 'js/view_profile.min.js',
        },
        'edit_reports': {
            'source_filenames': (
                'events/js/edit_ng_report.js',
            ),
            'output_filename': 'js/edit_reports.min.js',
        },
        'list_reports': {
            'source_filenames': (
                'reports/js/reports_list.js',
            ),
            'output_filename': 'js/reports_list.min.js',
        },
        'view_reports': {
            'source_filenames': (
                'reports/js/profiles_view_report.js',
            ),
            'output_filename': 'js/profiles_view_report.min.js',
        },
        'edit_voting': {
            'source_filenames': (
                'base/js/handlebars-v3.0.3.js'
                'voting/js/voting_edit_voting.js',
            ),
            'output_filename': 'js/edit_voting.min.js',
        },
        'list_voting': {
            'source_filenames': (
                'base/js/stupidtable.js'
                'voting/js/voting_list.js',
            ),
            'output_filename': 'js/list_voting.min.js',
        },
        'view_voting': {
            'source_filenames': (
                'voting/js/voting_view_voting.js',
            ),
            'output_filename': 'js/view_voting.min.js',
        },
        '404_js': {
            'source_filenames': (
                'base/js/404.js',
            ),
            'output_filename': 'js/404_js.min.js',
        },
    },
    'STYLESHEETS': {
        'base': {
            'source_filenames': (
                'browserid/persona-buttons.css',
                'base/css/*.css',
                'base/css/*.less',
            ),
            'output_filename': 'css/base.min.js',
            'extra_context': {
                'media': 'screen,projection,tv,print'
            }
        },
        'dashboard': {
            'source_filenames': (
                'dashboard/css/kpi.css',
            ),
            'output_filename': 'css/dashboard.min.css',
            'extra_context': {
                'media': 'screen,projection,tv,print'
            }
        },
        'mapbox_stylesheet': {
            'source_filenames': (
                'base/css/mapbox.css',
                'base/css/L.Control.Locate.css',
            ),
            'output_filename': 'css/edit_events.min.css',
            'extra_context': {
                'media': 'screen,projection,tv,print'
            }
        },
        'timeline_stylesheet': {
            'source_filenames': (
                'events/css/timeline/timeline.css',
            ),
            'output_filename': 'css/list_events.min.css',
            'extra_context': {
                'media': 'screen,projection,tv,print'
            }
        },
        'jquery_ui_custom_stylesheet': {
            'source_filenames': (
                'events/css/jquery-ui-1.10.0.custom.css',
            ),
            'output_filename': 'css/jquery-ui-custom.min.css',
            'extra_context': {
                'media': 'screen,projection,tv,print'
            }
        },
    }
}

PIPELINE_ENABLED = True
PIPELINE_DISABLE_WRAPPER = True
# TODO: install yuglify
# CSS_COMPRESSOR = 'pipeline.compressor.yuglify.YuglifyCompressor'
# JS_COMPRESSOR = 'pipeline.compressor.yuglify.YuglifyCompressor'

PIPELINE['COMPILERS'] = (
    'pipeline.compilers.less.LessCompiler',
)
