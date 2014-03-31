import json
import os
import urlparse

from . import base


vcap_application = json.loads(os.environ['VCAP_APPLICATION'])

DB_URL = os.environ.get('DATABASE_URL')
if DB_URL:
    url = urlparse.urlparse(DB_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port,
            'OPTIONS': {
                'init_command': 'SET storage_engine=InnoDB',
                'charset' : 'utf8',
                'use_unicode' : True,
            },
            'TEST_CHARSET': 'utf8',
            'TEST_COLLATION': 'utf8_general_ci',
        },
    }

# Recipients of traceback emails and other notifications.
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

# Debugging displays nice error messages, but leaks memory. Set this to False
# on all server instances and True only for development.
DEBUG = TEMPLATE_DEBUG = False

# Disable CSS/JS compression for development
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

# Is this a development instance? Set this to True on development/master
# instances and False on stage/prod.
DEV = False

# Playdoh ships with Bcrypt+HMAC by default because it's the most secure.
# To use bcrypt, fill in a secret HMAC key. It cannot be blank.
HMAC_KEYS = {
    '2012-06-06': os.environ.get('HMAC_KEY'),
}

# Cache backend settings. Enables Cache Machine's memcache backend.
CACHE_URL = os.environ.get('MEMCACHE_URL')
if CACHE_URL:
    CACHES = {
        'default': {
            'BACKEND': 'caching.backends.memcached.MemcachedCache',
            'LOCATION': CACHE_URL,
        }
    }

from django_sha2 import get_password_hashers
PASSWORD_HASHERS = get_password_hashers(base.BASE_PASSWORD_HASHERS, HMAC_KEYS)

# Make this unique, and don't share it with anybody.  It cannot be blank.
SECRET_KEY = os.environ.get('SECRET_KEY')

SESSION_COOKIE_SECURE = True

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery configuration
CELERY_ALWAYS_EAGER = True

# Uncomment the following line for local development, or BrowserID
# will fail to log you in.
# This might also need some extra ALLOWED_HOSTS (proxy IP) depending on the PaaS
# routing of HTTP requests.

ALLOWED_HOSTS = vcap_application['uris']
SITE_URL = 'https://%s' % ALLOWED_HOSTS[0]

# STATSD_CLIENT = 'django_statsd.clients.log'
# STATSD_PREFIX = 'reps'

COMPRESS_PRECOMPILERS = (
    ('text/less', '$HOME/node_modules/less/bin/lessc {infile} {outfile}'),
)

# HTTP proxy configuration. Uncomment if you are using HTTPS.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Remozilla configuration
# REMOZILLA_USERNAME = ''
# REMOZILLA_PASSWORD = ''

# Mailhide configuration
# Demo keys, replace with valid ones.
# MAILHIDE_PUB_KEY = '02Ni54q--g1yltekhaSmPYHQ=='
# MAILHIDE_PRIV_KEY = 'fe55a9921917184732077e3fed19d0be'

# Mozillians configuration
# MOZILLIANS_API_APPNAME = ''
# MOZILLIANS_API_KEY = ''
