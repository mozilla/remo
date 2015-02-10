from . import base

from django_sha2 import get_password_hashers

SITE_URL = 'http://127.0.0.1:8000'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'remo',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
            'init_command': 'SET storage_engine=InnoDB',
            'charset': 'utf8',
            'use_unicode': True,
        },
        'TEST_CHARSET': 'utf8',
        'TEST_COLLATION': 'utf8_general_ci',
    },
}

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

# Debugging displays nice error messages, but leaks memory. Set this to False
# on all server instances and True only for development.
DEBUG = TEMPLATE_DEBUG = True

# Disable CSS/JS compression for development
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False

# Is this a development instance? Set this to True on development/master
# instances and False on stage/prod.
DEV = True

# Playdoh ships with Bcrypt+HMAC by default because it's the most secure.
# To use bcrypt, fill in a secret HMAC key. It cannot be blank.
HMAC_KEYS = {
    '2012-06-06': 'some secret',
}

# Cache backend settings. Enables Cache Machine's memcache backend.
CACHES = {
    'default': {
        'BACKEND': 'caching.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

PASSWORD_HASHERS = get_password_hashers(base.BASE_PASSWORD_HASHERS, HMAC_KEYS)

# Make this unique, and don't share it with anybody.  It cannot be blank.
SECRET_KEY = 'some secret'

SESSION_COOKIE_SECURE = False

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MOZILLIANS_API_APPNAME = 'demo'
MOZILLIANS_API_KEY = 'demo'

MAILHIDE_PUB_KEY = '02Ni54q--g1yltekhaSm23HQ=='
MAILHIDE_PRIV_KEY = 'fe55a9921917184732012e3fed19d0be'
