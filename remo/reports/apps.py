from django.apps import AppConfig
from django.db.models.signals import post_migrate

from remo.base.utils import add_permissions_to_groups


def report_set_groups(sender, **kwargs):
    """Set permissions to groups."""
    app_label = sender.label
    if (isinstance(app_label, basestring) and app_label != 'reports'):
        return True

    perms = {'add_ngreport': ['Admin', 'Mentor'],
             'change_ngreport': ['Admin', 'Mentor'],
             'delete_ngreport': ['Admin', 'Mentor'],
             'delete_ngreportcomment': ['Admin', 'Mentor']}

    add_permissions_to_groups('reports', perms)


class ReportsConfig(AppConfig):
    name = 'remo.reports'
    label = 'reports'
    verbose_name = 'ReMo Reports'

    def ready(self):
        post_migrate.connect(report_set_groups, sender=self)
