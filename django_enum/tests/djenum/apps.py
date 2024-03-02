from django.apps import AppConfig


class DJEnumConfig(AppConfig):
    name = "django_enum.tests.djenum"
    label = name.replace(".", "_")
