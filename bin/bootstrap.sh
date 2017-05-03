#!/bin/bash
set -e

export MESOS_CLUSTER=True
export `cat env-dist | sed s/\ =\ /=/ | grep -v ^\# | xargs`
rm -rf .git
python manage.py collectstatic --noinput
python manage.py compress --force --engine jinja2 --extension=.jinja
