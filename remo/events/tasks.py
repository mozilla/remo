from datetime import datetime, timedelta

from celery.task import periodic_task

from remo.base.tasks import send_remo_mail
from remo.base.utils import get_date
from remo.events.models import Event


@periodic_task(run_every=timedelta(days=1))
def notify_event_owners_to_input_metrics():
    """Send an email to event creators.

    After an event has finished event creators are notified
    that they should input the actual metrics for the event.
    """
    start = datetime.combine(get_date(days=-1), datetime.min.time())
    end = datetime.combine(get_date(days=-1), datetime.max.time())
    events = Event.objects.filter(end__range=[start, end],
                                  has_new_metrics=True,
                                  eventmetricoutcome__outcome__isnull=True)
    events = events.distinct()

    for event in events:
        subject = ('[Reminder] Please add the actual metrics for event {0}'
                   .format(event.name))
        template = 'email/event_creator_notification_to_input_metrics.txt'
        data = {'event': event}
        send_remo_mail(subject=subject, email_template=template,
                       recipients_list=[event.owner.id], data=data)
