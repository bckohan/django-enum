from django.apps import AppConfig


class EnumPropConfig(AppConfig):
    name = "tests.dataclass"
    label = name.replace(".", "_")
