from django.apps import AppConfig
from django.db.models.signals import post_migrate

from remo.base.utils import add_permissions_to_groups


def voting_set_groups(sender, **kwargs):
    """Set permissions to groups."""
    app_label = sender.label
    if (isinstance(app_label, basestring) and app_label != 'voting'):
        return True

    permissions = {'add_poll': ['Admin', 'Council', 'Mentor'],
                   'delete_poll': ['Admin', 'Council', 'Mentor'],
                   'change_poll': ['Admin', 'Council', 'Mentor'],
                   'delete_pollcomment': ['Admin']}

    add_permissions_to_groups('voting', permissions)


class VotingConfig(AppConfig):
    name = 'remo.voting'
    label = 'voting'
    verbose_name = 'ReMo Voting'

    def ready(self):
        post_migrate.connect(voting_set_groups, self)
