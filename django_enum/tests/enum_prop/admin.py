from django.contrib import admin
from django_enum.tests.enum_prop.models import EnumTester, BitFieldModel

admin.site.register(EnumTester)
admin.site.register(BitFieldModel)
