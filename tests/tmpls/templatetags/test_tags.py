from enum import Enum, Flag
from django_enum.utils import decompose, get_set_values, get_set_bits
from django import template

register = template.Library()


@register.filter(name="is_enum")
def is_enum(instance):
    return isinstance(instance, Enum)


@register.filter(name="to_str")
def to_str(value):
    if value is None:
        return ""
    return str(value)


@register.filter(name="flags_str")
def flags_str(value):
    if not value:
        return ""
    if isinstance(value, Flag):
        labeled = decompose(value)
        values = {en.value for en in labeled}
        extra_values = [val for val in get_set_values(value) if val not in values]
        return "|".join(
            [en.name for en in labeled] + [str(val) for val in extra_values]
        )
    return "|".join([str(bit) for bit in get_set_bits(value)])
