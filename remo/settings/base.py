# This is your project's main settings file that can be committed to your
# repo. If you need to override a setting locally, use settings_local.py
from funfactory.settings_base import *  # noqa

# Defines the views served for root URLs.
ROOT_URLCONF = 'remo.urls'

INSTALLED_APPS = (['south'] +
                  list(INSTALLED_APPS) + [
                      # Application base, containing global templates.
                      'django.contrib.admin',
                      'django.contrib.messages',
                      'django.contrib.markup',

                      'remo.base',
                      'remo.profiles',
                      'remo.featuredrep',
                      'remo.remozilla',
                      'remo.reports',
                      'remo.api',
                      'remo.events',
                      'remo.voting',

                      'django_browserid',
                      'jingo_offline_compressor',
                      'tastypie',
                      'waffle',
                      'import_export'])

# Because Jinja2 is the default template loader, add any non-Jinja templated
# apps here:
JINGO_EXCLUDE_APPS = [
    'admin',
    'registration',
    'browserid',
]

# Tells the extract script what files to look for L10n in and what function
# handles the extraction. The Tower library expects this.

# # Use this if you have localizable HTML files:
# DOMAIN_METHODS['lhtml'] = [
#    ('**/templates/**.lhtml',
#        'tower.management.commands.extract.extract_tower_template'),
# ]

# # Use this if you have localizable HTML files:
# DOMAIN_METHODS['javascript'] = [
#    # Make sure that this won't pull in strings from external libraries you
#    # may use.
#    ('media/js/**.js', 'javascript'),
# ]

LOGGING = dict(loggers=dict(playdoh={'level': logging.DEBUG}))

# Add BrowserID as authentication backend
AUTHENTICATION_BACKENDS = ('django_browserid.auth.BrowserIDBackend',
                           'django.contrib.auth.backends.ModelBackend')

# Required for BrowserID. Very important security feature
SITE_URL = 'https://reps.mozilla.org'

# Override BrowserID verification
BROWSERID_VERIFY_CLASS = 'remo.base.views.BrowserIDVerify'

# Do not create user on login
BROWSERID_CREATE_USER = False

# Optional BrowserID settings
LOGIN_REDIRECT_URL = '/dashboard/'
LOGIN_REDIRECT_URL_FAILURE = '/'
LOGOUT_REDIRECT_URL = '/'


# Remove LocaleURLMiddleware since we are not localing our website
MIDDLEWARE_CLASSES = filter(
    lambda x: x != 'funfactory.middleware.LocaleURLMiddleware',
    MIDDLEWARE_CLASSES)

MIDDLEWARE_CLASSES += (
    'django.contrib.messages.middleware.MessageMiddleware',
    'remo.base.middleware.RegisterMiddleware',
    'waffle.middleware.WaffleMiddleware'
)

TEMPLATE_CONTEXT_PROCESSORS += (
    'django_browserid.context_processors.browserid',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages')

# Instruct session-csrf to always produce tokens for anonymous users
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

ETHERPAD_URL = 'http://etherpad.mozilla.org/'
ETHERPAD_PREFIX = 'remo-'

CONTRIBUTE_URL = ('http://www.mozilla.org/contribute/'
                  'event/?callbackurl=%(callbackurl)s')


REPS_MENTORS_LIST = 'reps-mentors@lists.mozilla.org'
REPS_COUNCIL_ALIAS = 'reps-council@mozilla.com'

# Mozillians API
MOZILLIANS_API_BASE = 'https://mozillians.org'

ALLOWED_HOSTS = ['reps.mozilla.org']

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

jinja_conf = JINJA_CONFIG()


def JINJA_CONFIG():
    jinja_conf['extensions'].append('caching.ext.cache')
    return jinja_conf

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'UTC'

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True


def _request_args():
    from django.conf import settings
    from tower import ugettext_lazy as _lazy

    args = {'siteName': _lazy('Mozilla Reps'), }

    if settings.SITE_URL.startswith('https'):
        args['siteLogo'] = '/static/base/img/remo/remo_logo_medium.png'

    return args
BROWSERID_REQUEST_ARGS = lazy(_request_args, dict)()

# Statsd Graphite
STATSD_CLIENT = 'django_statsd.clients.normal'

# Paginator settings
ITEMS_PER_PAGE = 25

# django-celery setup
import djcelery
djcelery.setup_loader()

MAPBOX_TOKEN = 'examples.map-vyofok3q'

SERVER_EMAIL = 'reps-dev@mozilla.com'
