from django.apps import AppConfig


class DJEnumConfig(AppConfig):
    name = "tests.djenum"
    label = name.replace(".", "_")
