#!/bin/bash
set -e

export MESOS_CLUSTER=True
export `cat remo/settings/env-dist | sed s/\ =\ /=/ | grep -v ^\# | xargs`
python manage.py collectstatic --noinput
python manage.py compress --force --engine jinja2 --extension=.jinja
