# This is your project's main settings file that can be committed to your
# repo. If you need to override a setting locally, use settings_local.py
from funfactory.settings_base import *

# Defines the views served for root URLs.
ROOT_URLCONF = 'remo.urls'

INSTALLED_APPS = ['south'] + \
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
                     'tastypie',
                     'waffle']

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

# Set profile module
AUTH_PROFILE_MODULE = 'profiles.UserProfile'

# Add BrowserID as authentication backend
AUTHENTICATION_BACKENDS = ('django_browserid.auth.BrowserIDBackend',
                           'django.contrib.auth.backends.ModelBackend',
                           )

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

MIDDLEWARE_CLASSES += ('django.contrib.messages.middleware.MessageMiddleware',
                       'remo.base.middleware.RegisterMiddleware',
                       'waffle.middleware.WaffleMiddleware')

TEMPLATE_CONTEXT_PROCESSORS += (
    'django_browserid.context_processors.browserid',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages')

# Instruct session-csrf to always produce tokens for anonymous users
ANON_ALWAYS = True

FROM_EMAIL = 'The ReMoBot <reps@mozilla.com>'

ADMINS = (
    ('Mozilla Reps', 'reps@mozilla.com'),
)

MANAGERS = ADMINS

# Allow robots to crawl the site.
ENGAGE_ROBOTS = True

CLOUDMADE_API = 'bbb9265287234b89b116cdbb09f0af36'
CLOUDMADE_MARKER_PURPLE = 'fc2feea1e8e84d0192c32a2b867073a3'
CLOUDMADE_MARKER = '9d7b9835ddd64784ade32d16a7968e90'
CLOUDMADE_MARKER_75 = '43d850f01ff24721bbdc7a9fa31bd829'
CLOUDMADE_MARKER_85 = '507f4f059b1b4e2b939afd14d327ccbb'

USE_TZ = True

ETHERPAD_URL = 'http://etherpad.mozilla.org/'
ETHERPAD_PREFIX = 'remo-'

CONTRIBUTE_URL = ('http://www.mozilla.org/contribute/'
                  'event/?callbackurl=%(callbackurl)s')


REPS_MENTORS_LIST = 'reps-mentors@lists.mozilla.org'
REPS_COUNCIL_LIST = 'reps-council@mozilla.com'

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

COMPRESS_ENABLED = True
