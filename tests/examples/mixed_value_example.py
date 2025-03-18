from .models.mixed_value import MixedValueExample, MixedValueEnum
from django.db import models

obj = MixedValueExample.objects.create(
    eccentric_str=MixedValueEnum.NONE,
    eccentric_float=MixedValueEnum.NONE
)

assert isinstance(obj._meta.get_field("eccentric_str"), models.CharField)
assert isinstance(obj._meta.get_field("eccentric_float"), models.FloatField)

for en in list(MixedValueEnum):
    obj.eccentric_str = en
    obj.eccentric_float = en
    obj.save()
    obj.refresh_from_db()
    assert obj.eccentric_str is en
    assert obj.eccentric_float is en
    print(f"{obj.eccentric_str=}")
    print(f"{obj.eccentric_float=}")
