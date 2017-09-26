from django.apps import AppConfig


class RemozillaConfig(AppConfig):
    name = 'remo.remozilla'
    label = 'remozilla'
    verbose_name = 'ReMo Remozilla'

    def ready(self):
        import remo.remozilla.signals  # noqa
