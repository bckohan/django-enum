from django.contrib import admin

from tests.dataclass.models import (
    AdminDisplayBug35,
    EnumTester,
)


class AdminDisplayBug35Admin(admin.ModelAdmin):
    list_display = ("text_enum", "int_enum")
    readonly_fields = ("text_enum", "int_enum", "blank_int", "blank_txt")


admin.site.register(EnumTester)
admin.site.register(AdminDisplayBug35, AdminDisplayBug35Admin)
