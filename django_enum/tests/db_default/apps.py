from django.apps import AppConfig


class DBDefaultConfig(AppConfig):
    name = 'django_enum.tests.db_default'
    label = name.replace('.', '_')
