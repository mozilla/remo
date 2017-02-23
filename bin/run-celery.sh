#!/bin/sh

python manage.py migrate djcelery
celery -A remo worker -l INFO
