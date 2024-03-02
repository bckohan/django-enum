from django.apps import AppConfig


class FlagConstraintsConfig(AppConfig):
    name = "django_enum.tests.flag_constraints"
    label = name.replace(".", "_")
