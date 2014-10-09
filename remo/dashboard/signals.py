from django.dispatch import Signal

action_item_created = Signal(providing_args=['instance'])
action_item_resolved = Signal(
    providing_args=['instance', 'user', 'action_type']
)
