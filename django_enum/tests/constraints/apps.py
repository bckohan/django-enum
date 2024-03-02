from django.apps import AppConfig


class ConstraintsConfig(AppConfig):
    name = "django_enum.tests.constraints"
    label = name.replace(".", "_")
