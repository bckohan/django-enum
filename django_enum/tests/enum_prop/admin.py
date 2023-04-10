try:
    from django.contrib import admin
    from django_enum.tests.enum_prop.models import BitFieldModel, EnumTester

    admin.site.register(EnumTester)
    admin.site.register(BitFieldModel)

except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass
