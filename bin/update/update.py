"""
Deploy reps.mozilla.org using Chief in dev/stage/production.

Requires commander_ which is installed on the systems that need it.

.. _commander: https://github.com/oremj/commander
"""

import os
import sys
import urllib
import urllib2

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commander.deploy import task, hostgroups
import commander_settings as settings


NEW_RELIC_URL = 'https://rpm.newrelic.com/deployments.xml'
NEW_RELIC_APP_ID = getattr(settings, 'NEW_RELIC_APP_ID', False)
NEW_RELIC_API_KEY = getattr(settings, 'NEW_RELIC_API_KEY', False)


@task
def update_code(ctx, tag):
    """Update the code to a specific git reference (tag/sha/etc)."""
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('git fetch')
        ctx.local('git checkout -f %s' % tag)
        ctx.local('git submodule sync')
        ctx.local('git submodule update --init --recursive')
        ctx.local("find . -type f -name '.gitignore' -o -name '*.pyc' -delete")
        ctx.local('git clean -xdff "vendor-local/"')


@task
def update_assets(ctx):
    with ctx.lcd(settings.SRC_DIR):
        # LANG=en_US.UTF-8 is sometimes necessary for the YUICompressor.
        ctx.local('LANG=en_US.UTF8 python ./manage.py collectstatic --noinput')
        ctx.local('LANG=en_US.UTF8 python ./manage.py compress_jingo')


@task
def update_db(ctx):
    """Update the database schema, if necessary.

    """
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('python ./manage.py migrate')


@task
def update_product_details(ctx):
    """Update the product details

    """
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('python ./manage.py update_product_details ')


@task
def checkin_changes(ctx):
    """Use the local, IT-written deploy script to check in changes."""
    ctx.local(settings.DEPLOY_SCRIPT)


@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def deploy_app(ctx):
    """Call the remote update script to push changes to webheads."""
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)
    ctx.remote('/bin/touch %s' % settings.REMOTE_WSGI)


@hostgroups(settings.CELERY_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def update_celery(ctx):
    """Update and restart Celery."""
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)
    ctx.remote('/sbin/service %s restart' % settings.CELERY_SERVICE)
    ctx.remote('/sbin/service %s restart' % settings.CELERYBEAT_SERVICE)


@task
def update_info(ctx, tag):
    """Write info about the current state to a publicly visible file."""
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('date > static/revision_info.txt')
        ctx.local('git branch >> static/revision_info.txt')
        ctx.local('git log -3 >> static/revision_info.txt')
        ctx.local('git status >> static/revision_info.txt')
        ctx.local('git submodule status >> static/revision_info.txt')
        ctx.local('git rev-parse HEAD > static/revision.txt')

        if NEW_RELIC_API_KEY and NEW_RELIC_APP_ID:
            print 'Post deploy event to NewRelic'
            data = urllib.urlencode(
                {'deployment[revision]': tag,
                 'deployment[app_id]': NEW_RELIC_APP_ID})
            headers = {'x-api-key': NEW_RELIC_API_KEY}
            try:
                request = urllib2.Request(NEW_RELIC_URL, data, headers)
                urllib2.urlopen(request)
            except urllib.URLError as exp:
                print 'Error notifing NewRelic: {0}'.format(exp)


@task
def pre_update(ctx, ref=settings.UPDATE_REF):
    """Update code to pick up changes to this file."""
    update_code(ref)
    update_info(ref)


@task
def update(ctx):
    update_assets()
    update_db()


@task
def deploy(ctx):
    checkin_changes()
    deploy_app()
    update_celery()


@task
def update_site(ctx, tag):
    """Update the app to prep for deployment."""
    pre_update(tag)
    update()
