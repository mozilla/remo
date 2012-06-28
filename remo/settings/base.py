# This is your project's main settings file that can be committed to your
# repo. If you need to override a setting locally, use settings_local.py
from funfactory.settings_base import *

# Bundles is a dictionary of two dictionaries, css and js, which list css files
# and js files that can be bundled together by the minify app.
MINIFY_BUNDLES = {
    'css': {
        'common': (
            'css/remo/foundation.css',
            ),
        'common_ie': (
            'css/remo/ie.css',
            ),
        'remo': (
            'css/remo/app.less',
            ),
        'leaflet': (
            'leaflet/leaflet.css',
            )
    },
    'js': {
        'less': (
            'js/less-1.3.0.min.js',
            ),
        'common-dbg': (
            'js/jquery-1.7.1.js',
            'js/modernizr.foundation.js',
            'js/foundation.js',
            'js/activate.browserid.js',
            'js/jquery.prettydate.js',
             # Our app.js is always last to override stuff
            'js/app.js',
            ),
        'common': (
            'js/jquery.min.js',
            'js/modernizr.foundation.js',
            'js/foundation.js',
            'js/activate.browserid.js',
            'js/jquery.prettydate.js',
             # Our app.js is always last to override stuff
            'js/app.js',
            ),
        'tracker': (
            'js/tracker.load.js',
            ),
        'tracker-full': (
            'js/tracker.js',
            ),
        'profiles_people': (
            'js/jquery.tmpl.js',
            'js/profiles_people.js'
            ),
        'leaflet': (
            'leaflet/leaflet.js',
            ),
        'profiles_edit_profile': (
            'js/profiles_edit_profile.js',
            ),
        'base_dashboard': (
            'js/stupidtable.js',
            'js/dashboard.js'
            ),
        'profiles_view_report': (
            'js/profiles_view_report.js',
            ),
    }
}

# Defines the views served for root URLs.
ROOT_URLCONF = 'remo.urls'

INSTALLED_APPS = ['south'] + \
                 list(INSTALLED_APPS) + [
                     # Application base, containing global templates.
                     'django.contrib.admin',
                     'django.contrib.messages',
                     'django.contrib.markup',
                     'jingo_minify',

                     'remo.base',
                     'remo.profiles',
                     'remo.featuredrep',
                     'remo.remozilla',
                     'remo.reports',
                     'remo.api',

                     'django_browserid',
                     'tastypie',

                     ]

# Because Jinja2 is the default template loader, add any non-Jinja templated
# apps here:
JINGO_EXCLUDE_APPS = [
    'admin',
    'registration',
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

LOGGING = dict(loggers=dict(playdoh = {'level': logging.DEBUG}))

# Set profile module
AUTH_PROFILE_MODULE = 'profiles.UserProfile'

# Add BrowserID as authentication backend
AUTHENTICATION_BACKENDS = ('django_browserid.auth.BrowserIDBackend',
                           'django.contrib.auth.backends.ModelBackend',
                           )

# Required for BrowserID. Very important security feature
SITE_URL = 'https://reps.mozilla.org'

# Remove LocaleURLMiddleware since we are not localing our website
MIDDLEWARE_CLASSES = filter(
    lambda x: x != 'funfactory.middleware.LocaleURLMiddleware',
    MIDDLEWARE_CLASSES)

MIDDLEWARE_CLASSES += ('django.contrib.messages.middleware.MessageMiddleware',
                       'remo.base.middleware.RegisterMiddleware')

TEMPLATE_CONTEXT_PROCESSORS += (
    'django_browserid.context_processors.browserid_form',
    'django.contrib.messages.context_processors.messages')

# Instruct session-csrf to always produce tokens for anonymous users
ANON_ALWAYS = True

LOGIN_REDIRECT_URL_FAILURE = '/login/failed/'

FROM_EMAIL = 'reps@mozilla.com'

ADMINS = (
    ('Mozilla Reps', 'reps@mozilla.com'),
)

MANAGERS = ADMINS

CLOUDMADE_API = 'b465ca1b6fe040dba7eec0291ecb7a8c'
CLOUDMADE_MARKER_PURPLE = 'fc2feea1e8e84d0192c32a2b867073a3'
CLOUDMADE_MARKER = '9d7b9835ddd64784ade32d16a7968e90'
CLOUDMADE_MARKER_75 = '43d850f01ff24721bbdc7a9fa31bd829'
CLOUDMADE_MARKER_85 = '507f4f059b1b4e2b939afd14d327ccbb'

USE_TZ = True
