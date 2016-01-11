"""
WSGI config for ReMo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'remo.settings')  # NOQA
os.environ.setdefault('CELERY_LOADER', 'django')  # NOQA

from django.conf import settings
from django.core.wsgi import get_wsgi_application

import newrelic
from decouple import config


application = get_wsgi_application()


# Add NewRelic
newrelic_ini = config('NEW_RELIC_CONFIG_FILE', default='newrelic.ini')
newrelic_license_key = config('NEW_RELIC_LICENSE_KEY', default=None)
if newrelic_ini and newrelic_license_key:
    newrelic.agent.initialize(newrelic_ini)
    application = newrelic.agent.wsgi_application()(application)
