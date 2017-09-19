#!/bin/sh

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py compress --engine jinja2 --extension=.jinja
gunicorn remo.wsgi:application -w 3 -b 0.0.0.0:${PORT:-8000} --log-file -
