import enum_properties
from django.apps import AppConfig


class EnumPropConfig(AppConfig):
    name = "tests.enum_prop"
    label = name.replace(".", "_")
