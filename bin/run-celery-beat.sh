#!/bin/sh

python manage.py migrate djcelery
celery -A remo beat -l INFO
