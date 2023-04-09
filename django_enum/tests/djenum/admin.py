from django.contrib import admin
from django_enum.tests.djenum.models import AdminDisplayBug35, EnumTester

admin.site.register(EnumTester)


class AdminDisplayBug35Admin(admin.ModelAdmin):

    list_display = ('text_enum', 'int_enum')
    readonly_fields = ('text_enum', 'int_enum')


admin.site.register(AdminDisplayBug35, AdminDisplayBug35Admin)
