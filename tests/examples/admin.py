import sys
from django.contrib import admin

from tests.examples.models import (
    Map,
    BasicExample,
    FlagExample,
    NoCoerceExample,
    StrictExample,
    PropertyExample,
    ChoicesWithProperties,
    TextChoicesExample
)

admin.site.register(Map)
admin.site.register(StrictExample)
admin.site.register(NoCoerceExample)
admin.site.register(PropertyExample)
admin.site.register(BasicExample)
admin.site.register(FlagExample)
admin.site.register(ChoicesWithProperties)
admin.site.register(TextChoicesExample)
