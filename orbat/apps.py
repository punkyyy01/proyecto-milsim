from django.apps import AppConfig


class OrbatConfig(AppConfig):
    name = 'orbat'

    def ready(self):
        import orbat.signals
