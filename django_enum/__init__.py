r"""
*******************************************************************************
   ___    _                       ____
  / _ \  (_)__ ____  ___ ____    / __/__  __ ____ _
 / // / / / _ `/ _ \/ _ `/ _ \  / _// _ \/ // /  ' \
/____/_/ /\_,_/_//_/\_, /\___/ /___/_//_/\_,_/_/_/_/
    |___/          /___/

*******************************************************************************
"""
from django_enum.choices import (
    DjangoEnumPropertiesMeta,
    FlagChoices,
    FloatChoices,
    IntegerChoices,
    TextChoices,
)
from django_enum.converters import register_enum_converter
from django_enum.fields import EnumField, FlagField
from django_enum.filters import EnumFilter, FilterSet
from django_enum.forms import (
    EnumChoiceField,
    EnumFlagField,
    NonStrictSelect,
    NonStrictSelectMultiple,
)

__all__ = [
    'EnumField',
    'FlagField',
    'TextChoices',
    'IntegerChoices',
    'FlagChoices',
    'FloatChoices',
    'DjangoEnumPropertiesMeta',
    'EnumChoiceField',
    'EnumFlagField',
    'FilterSet',
    'EnumFilter',
    'NonStrictSelect',
    'NonStrictSelectMultiple',
    'register_enum_converter'
]

VERSION = (2, 0, 0)

__title__ = 'Django Enum'
__version__ = '.'.join(str(i) for i in VERSION)
__author__ = 'Brian Kohan'
__license__ = 'MIT'
__copyright__ = 'Copyright 2022-2023 Brian Kohan'
