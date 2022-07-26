try:
    import enum_properties
    from django.apps import AppConfig


    class EnumPropConfig(AppConfig):
        name = 'django_enum.tests.enum_prop'
        label = name.replace('.', '_')

except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass
