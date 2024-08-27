from django.contrib import admin

from tests.djenum.models import AdminDisplayBug35, EnumTester

admin.site.register(EnumTester)


class AdminDisplayBug35Admin(admin.ModelAdmin):

    list_display = ("text_enum", "int_enum")
    readonly_fields = ("text_enum", "int_enum", "blank_int", "blank_txt")


admin.site.register(AdminDisplayBug35, AdminDisplayBug35Admin)
