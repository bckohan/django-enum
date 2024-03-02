from enum import Enum

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
