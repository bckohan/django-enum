from django.contrib import admin
from django_enum.tests.examples.models import (
    Map,
    StrictExample,
    NoCoerceExample,
    TextChoicesExample,
    MyModel,
    BitFieldExample
)


admin.site.register(Map)
admin.site.register(StrictExample)
admin.site.register(NoCoerceExample)
admin.site.register(TextChoicesExample)
admin.site.register(MyModel)
admin.site.register(BitFieldExample)
