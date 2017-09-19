from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = 'remo.dashboard'
    label = 'dashboard'
    verbose_name = 'ReMo Dashboard'

    def ready(self):
        import remo.dashboard.signals # noqa
