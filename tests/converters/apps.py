from django.apps import AppConfig


class Converters(AppConfig):
    name = "tests.converters"
    label = name.replace(".", "_")
