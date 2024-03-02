from django.apps import AppConfig


class BenchmarkConfig(AppConfig):
    name = "django_enum.tests.benchmark"
    label = name.replace(".", "_")
