from django.apps import AppConfig


class DBDefaultConfig(AppConfig):
    name = "tests.db_default"
    label = name.replace(".", "_")
