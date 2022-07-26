from django.apps import AppConfig


class EditTestsConfig(AppConfig):
    name = 'django_enum.tests.edit_tests'
    label = name.replace('.', '_')
