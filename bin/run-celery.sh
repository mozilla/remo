#!/bin/sh

python manage.py migrate django-celery
celery -A remo worker -l INFO
