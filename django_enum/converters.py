"""
A metaclass and converter for Django's URL dispatcher to use with Python's
Enum class.
"""
from decimal import DecimalException
from enum import Enum
from typing import Type

from django.urls.converters import register_converter
from django_enum.utils import determine_primitive

__all__ = ['register_enum_converter']


class _EnumConverter:

    enum: Type[Enum]
    prop: str = 'value'
    primitive: type

    def to_python(self, value: str) -> Enum:
        """
        Attempt coercion of value to enumeration type instance, if unsuccessful
        and non-strict, coercion to enum's primitive type will be done,
        otherwise a ValueError is raised.
        """
        try:
            return self.enum(value)  # pylint: disable=E1102
        except (TypeError, ValueError):
            try:
                value = self.primitive(value)
                return self.enum(value)  # pylint: disable=E1102
            except (TypeError, ValueError, DecimalException):
                return self.enum[value]

    def to_url(self, value):
        """
        Convert the given enumeration value to its url string.

        :param value: The enumeration value
        :return: the string representation of the enumeration value
        """
        return str(getattr(value, self.prop))


def register_enum_converter(enum: Type[Enum], type_name='', prop='value'):
    """
    Register an enum converter for Django's URL dispatcher.

    :param enum: The enumeration type to register.
    :param type_name: the name to use for the converter
    :param prop: The property name to use to generate urls - by default the
        value is used.
    """
    register_converter(
        type(
            f'{enum.__name__}Converter',
            (_EnumConverter,),
            {
                'enum': enum,
                'prop': prop,
                'primitive': determine_primitive(enum),
                'regex': '|'.join([str(getattr(env, prop)) for env in enum])
            }
        ),
        type_name or enum.__name__
    )
