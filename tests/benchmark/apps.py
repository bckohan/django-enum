from django.apps import AppConfig


class BenchmarkConfig(AppConfig):
    name = "tests.benchmark"
    label = name.replace(".", "_")
