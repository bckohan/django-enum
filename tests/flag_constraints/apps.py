from django.apps import AppConfig


class FlagConstraintsConfig(AppConfig):
    name = "tests.flag_constraints"
    label = name.replace(".", "_")
