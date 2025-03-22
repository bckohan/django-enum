from django.contrib import admin

from django.forms import ModelForm
from tests.djenum.models import (
    AdminDisplayBug35,
    EnumTester,
    NullBlankFormTester,
    NullableBlankFormTester,
    Bug53Tester,
    NullableStrFormTester,
)

admin.site.register(EnumTester)
admin.site.register(NullBlankFormTester)
admin.site.register(NullableBlankFormTester)
admin.site.register(Bug53Tester)
admin.site.register(NullableStrFormTester)


class AdminDisplayBug35Admin(admin.ModelAdmin):
    list_display = ("text_enum", "int_enum")
    readonly_fields = ("text_enum", "int_enum", "blank_int", "blank_txt")


admin.site.register(AdminDisplayBug35, AdminDisplayBug35Admin)
