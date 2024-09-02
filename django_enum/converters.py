"""
A metaclass and converter for Django's URL dispatcher to use with Python's
Enum class.
"""

from enum import Enum
from typing import Dict, Optional, Type, Union, cast

from django.urls.converters import register_converter

from django_enum.utils import ValueGetter, determine_primitive

__all__ = ["register_enum_converter"]


class _EnumConverter:
    enum: Type[Enum]
    prop: str = "value"
    primitive: type

    _lookup_: Dict[str, Enum]

    def to_python(self, value: str) -> Enum:
        """
        Convert the string representation of the enum into an instance of it.
        """
        return self._lookup_[value]

    def to_url(self, value):
        """
        Convert the given enumeration value to its url string.

        :param value: The enumeration value
        :return: the string representation of the enumeration value
        """
        return str(getattr(value, self.prop))


def register_enum_converter(
    enum: Type[Enum],
    type_name="",
    prop="value",
    value: Optional[Union[str, ValueGetter]] = None,
):
    """
    Register an enum converter for Django's URL dispatcher.

    :param enum: The enumeration type to register.
    :param type_name: the name to use for the converter
    :param prop: The property name to use to generate urls - by default the
        value is used.
    :param value: The property or method to use to get the primitive value
        from the enumeration instance (if different than "value").
    """
    register_converter(
        type(
            f"{enum.__name__}Converter",
            (_EnumConverter,),
            {
                "enum": enum,
                "prop": prop,
                "primitive": determine_primitive(
                    enum,
                    value=cast(ValueGetter, lambda e: getattr(e, value))
                    if isinstance(value, str)
                    else value,
                ),
                "regex": "|".join([str(getattr(env, prop)) for env in enum]),
                "_lookup_": {str(getattr(env, prop)): env for env in enum},
            },
        ),
        type_name or enum.__name__,
    )
