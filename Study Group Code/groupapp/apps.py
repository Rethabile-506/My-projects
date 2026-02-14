from django.apps import AppConfig


class GroupappConfig(AppConfig):
    name = 'groupapp'

    def ready(self):
        import groupapp.signals
