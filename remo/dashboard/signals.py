from django.db.models.signals import post_save

from remo.dashboard.models import ActionItem
from remo.remozilla.models import Bug


post_save.connect(ActionItem.create, sender=Bug, dispatch_uid='create_action_items_bugzilla_sig')
