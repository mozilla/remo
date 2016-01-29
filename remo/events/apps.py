from django.apps import AppConfig
from django.db.models.signals import post_migrate

from remo.base.utils import add_permissions_to_groups


def event_set_groups(sender, **kwargs):
    """Set permissions to groups."""
    app_label = sender.label
    if (isinstance(app_label, basestring) and app_label != 'events'):
        return True

    perms = {'can_edit_events': ['Admin', 'Council', 'Mentor', 'Rep'],
             'can_delete_events': ['Admin', 'Council', 'Mentor'],
             'can_delete_event_comments': ['Admin'],
             'can_subscribe_to_events': ['Admin', 'Council', 'Mentor', 'Rep',
                                         'Alumni', 'Mozillians']}

    add_permissions_to_groups('events', perms)


class EventsConfig(AppConfig):
    name = 'remo.events'
    label = 'events'
    verbose_name = 'ReMo Events'

    def ready(self):
        post_migrate.connect(event_set_groups, sender=self)
