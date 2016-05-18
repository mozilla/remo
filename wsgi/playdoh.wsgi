"""
WSGI config for ReMo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""
import os
import site

from django.core.wsgi import get_wsgi_application
try:
    import newrelic.agent
except ImportError:
    newrelic = False

if newrelic:
    newrelic_ini = os.getenv('NEWRELIC_PYTHON_INI_FILE', False)
    if newrelic_ini:
        newrelic.agent.initialize(newrelic_ini)
    else:
        newrelic = False

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'remo.settings')
os.environ.setdefault('CELERY_LOADER', 'django')

# Add `remo` to the python path
wsgidir = os.path.dirname(__file__)
site.addsitedir(os.path.abspath(os.path.join(wsgidir, '../')))

application = get_wsgi_application()

if newrelic:
    application = newrelic.agent.wsgi_application()(application)
