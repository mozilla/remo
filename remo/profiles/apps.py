from django.apps import AppConfig
from django.db.models.signals import post_migrate

from remo.base.utils import add_permissions_to_groups


def profiles_set_groups(sender, **kwargs):
    """Set permissions to groups."""
    app_label = sender.label
    if (isinstance(app_label, basestring) and app_label != 'profiles'):
        return True

    perms = {'create_user': ['Admin', 'Mentor'],
             'can_edit_profiles': ['Admin'],
             'can_delete_profiles': ['Admin']}

    add_permissions_to_groups('profiles', perms)


class ProfilesConfig(AppConfig):
    name = 'remo.profiles'
    label = 'profiles'
    verbose_name = 'ReMo Profiles'

    def ready(self):
        post_migrate.connect(profiles_set_groups, self)
