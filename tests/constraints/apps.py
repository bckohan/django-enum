from django.apps import AppConfig


class ConstraintsConfig(AppConfig):
    name = "tests.constraints"
    label = name.replace(".", "_")
