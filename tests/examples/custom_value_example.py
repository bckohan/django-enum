from .models.custom_value import CustomValueExample
from django.db import models

obj = CustomValueExample.objects.create(
    str_props=CustomValueExample.StrPropsEnum.STR2
)

assert isinstance(obj._meta.get_field("str_props"), models.CharField)
assert obj.str_props is CustomValueExample.StrPropsEnum.STR2
assert obj.str_props.value.upper == "STR2"
assert obj.str_props.value.lower == "str2"
print(f"{obj.str_props=}")
