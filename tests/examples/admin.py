from django.contrib import admin

from tests.examples.models import (
    BitFieldExample,
    Map,
    MyModel,
    NoCoerceExample,
    StrictExample,
    TextChoicesExample,
)

admin.site.register(Map)
admin.site.register(StrictExample)
admin.site.register(NoCoerceExample)
admin.site.register(TextChoicesExample)
admin.site.register(MyModel)
admin.site.register(BitFieldExample)
