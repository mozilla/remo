from django.dispatch import Signal

action_item_resolved = Signal(
    providing_args=['instance', 'user', 'action_type']
)
