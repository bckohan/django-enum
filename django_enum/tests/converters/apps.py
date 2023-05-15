from django.apps import AppConfig


class Converters(AppConfig):
    name = 'django_enum.tests.converters'
    label = name.replace('.', '_')
