from django.apps import AppConfig


class App1Config(AppConfig):
    name = 'django_enum.tests.enum_prop'
    label = name.replace('.', '_')

    def ready(self):
        pass
