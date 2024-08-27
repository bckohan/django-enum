from django.apps import AppConfig


class EditTestsConfig(AppConfig):
    name = "tests.edit_tests"
    label = name.replace(".", "_")
