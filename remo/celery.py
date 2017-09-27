from __future__ import absolute_import

import os

from celery import Celery as BaseCelery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'remo.settings')

from django.conf import settings  # noqa

RUN_DAILY = 60 * 60 * 24
RUN_HOURLY = 60 * 60


class Celery(BaseCelery):
    def on_configure(self):
        from raven.contrib.celery import register_signal, register_logger_signal
        from raven.contrib.django.raven_compat.models import client as raven_client

        register_logger_signal(raven_client)
        register_signal(raven_client)


app = Celery('remo')

app.add_defaults({
    'worker_hijack_root_logger': False
})
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from remo.base.tasks import celery_healthcheck
    from remo.events.tasks import notify_event_owners_to_input_metrics
    from remo.profiles.tasks import (check_mozillian_username, reset_rotm_nominees,
                                     send_rotm_nomination_reminder, set_unavailability_flag,
                                     resolve_nomination_action_items)
    from remo.remozilla.tasks import fetch_bugs
    from remo.reports.tasks import (send_first_report_notification, calculate_longest_streaks,
                                    send_second_report_notification, resolve_report_action_items)
    from remo.voting.tasks import extend_voting_period, resolve_action_items, create_rotm_poll

    sender.add_periodic_task(RUN_DAILY, notify_event_owners_to_input_metrics.s(),
                             name='notify-event-owners-to-input-metrics')

    sender.add_periodic_task(RUN_DAILY, check_mozillian_username.s(),
                             name='check-mozillian-username')

    sender.add_periodic_task(RUN_DAILY, reset_rotm_nominees.s(),
                             name='reset-rotm-nominees')

    sender.add_periodic_task(RUN_DAILY, send_rotm_nomination_reminder.s(),
                             name='send-rotm-nomination-reminder')

    sender.add_periodic_task(RUN_DAILY / 2, set_unavailability_flag.s(),
                             name='set-unavailability-flag')

    sender.add_periodic_task(RUN_DAILY, resolve_nomination_action_items.s(),
                             name='resolve-nomination-action-items')

    sender.add_periodic_task(RUN_HOURLY / 4, fetch_bugs.s(),
                             name='fetch-bugs')

    sender.add_periodic_task(RUN_DAILY, send_first_report_notification.s(),
                             name='send-first-report-notification')

    sender.add_periodic_task(RUN_DAILY, send_second_report_notification.s(),
                             name='send-second-report-notification')

    sender.add_periodic_task(RUN_DAILY, calculate_longest_streaks.s(),
                             name='calculate-longest-streaks')

    sender.add_periodic_task(RUN_DAILY, resolve_report_action_items.s(),
                             name='resolve-report-action-items')

    sender.add_periodic_task(RUN_DAILY / 3, extend_voting_period.s(),
                             name='extend-voting-period')

    sender.add_periodic_task(RUN_DAILY, resolve_action_items.s(),
                             name='resolve-action-items')

    sender.add_periodic_task(RUN_DAILY, create_rotm_poll.s(),
                             name='create-rotm-poll')

    sender.add_periodic_task(RUN_HOURLY, celery_healthcheck.s(),
                             name='celery-healthcheck')
