#!/bin/sh
# This script makes sure that Jenkins can properly run your tests against your
# codebase.
set -e

DB_HOST="localhost"
DB_USER="hudson"

cd $WORKSPACE
VENV=$WORKSPACE/venv

echo "Starting build on executor $EXECUTOR_NUMBER..."

# Make sure there's no old pyc files around.
find . -name '*.pyc' -exec rm {} \;

if [ ! -d "$VENV/bin" ]; then
  echo "No virtualenv found.  Making one..."
  virtualenv $VENV --no-site-packages
  source $VENV/bin/activate
  pip install --upgrade pip
  pip install coverage
  pip install django_coverage
fi

git submodule sync -q
git submodule update --init --recursive

if [ ! -d "$WORKSPACE/vendor" ]; then
    echo "No /vendor... crap."
    exit 1
fi

source $VENV/bin/activate
pip install -q -r requirements/compiled.txt
pip install -q -r requirements/dev.txt

cat > settings/local.py <<SETTINGS
from settings.base import *

LOG_LEVEL = logging.ERROR
# Database name has to be set because of sphinx
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '${DB_HOST}',
        'NAME': '${JOB_NAME}',
        'USER': 'hudson',
        'PASSWORD': '',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
        'TEST_NAME': 'test_${JOB_NAME}',
        'TEST_CHARSET': 'utf8',
        'TEST_COLLATION': 'utf8_general_ci',
    }
}

INSTALLED_APPS += ('django_nose', 'django_coverage')
CELERY_ALWAYS_EAGER = True

SECRET_KEY = 'jenkins secret'
HMAC_KEYS = {
    '2013-01-01': '2d03c44177c32011u7e4c2fbf40asd5277doiu6ad8e14e373b92c603b164e288d',
}
from django_sha2 import get_password_hashers
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Demo Keys don't work really.
MAILHIDE_PUB_KEY = '02Ni54q--g1yltekhaSm23HQ=='
MAILHIDE_PRIV_KEY = 'fe55a9921917184732012e3fed19d0be'

REMOZILLA_USERNAME='demo'
REMOZILLA_PASSWORD='demo'
MOZILLIANS_API_KEY='demo'
MOZILLIANS_API_APPNAME='demo'
SETTINGS

echo "Update product_details"
python manage.py update_product_details

echo "Database name: ${JOB_NAME}"
echo "Dropping database if it exists"
echo "DROP DATABASE IF EXISTS test_${JOB_NAME};"|mysql -u $DB_USER -h $DB_HOST

echo "Creating database if we need it..."
echo "CREATE DATABASE IF NOT EXISTS ${JOB_NAME}"|mysql -u $DB_USER -h $DB_HOST

echo "Starting tests..."
export FORCE_DB=1
if [ -z $COVERAGE ]; then
    python manage.py test --noinput --with-xunit --logging-clear-handlers
else
    python manage.py test_coverage --noinput
fi
echo "FIN"
