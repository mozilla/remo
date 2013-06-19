from django.dispatch import Signal

create_radio_poll_signal = Signal(providing_args=['bug'])
