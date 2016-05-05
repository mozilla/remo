from django.apps import AppConfig
from django.db.models.signals import post_migrate

from remo.base.utils import add_permissions_to_groups


def featuredrep_set_groups(sender, **kwargs):
    """Set permissions to groups."""
    app_label = sender.label
    if (isinstance(app_label, basestring) and app_label != 'featuredrep'):
        return True

    perms = {'can_edit_featured': ['Admin', 'Council'],
             'can_delete_featured': ['Admin', 'Council']}

    add_permissions_to_groups('featuredrep', perms)


class FeaturedrepConfig(AppConfig):
    name = 'remo.featuredrep'
    label = 'featuredrep'
    verbose_name = 'ReMo Featured Rep'

    def ready(self):
        post_migrate.connect(featuredrep_set_groups, self)
