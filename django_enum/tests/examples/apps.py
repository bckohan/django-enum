from django.apps import AppConfig


class ExamplesConfig(AppConfig):
    name = "django_enum.tests.examples"
    label = name.replace(".", "_")
