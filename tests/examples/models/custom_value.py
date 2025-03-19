from enum import Enum
from django.db import models
from django_enum import EnumField


class StrProps:
    """
    Wrap a string with some properties.
    """

    _str = ''

    def __init__(self, string):
        self._str = string

    def __str__(self):
        """
        coercion to str - str(StrProps('str1')) == 'str1'
        """
        return self._str

    @property
    def upper(self):
        return self._str.upper()

    @property
    def lower(self):
        return self._str.lower()

    def __eq__(self, other):
        """
        Make sure StrProps('str1') == 'str1'
        """
        if isinstance(other, str):
            return self._str == other
        if other is not None:
            return self._str == other._str
        return False

    def deconstruct(self):
        """
        Necessary to construct choices and default in migration files
        """
        return (
            f'{self.__class__.__module__}.{self.__class__.__qualname__}',
            (self._str,),
            {}
        )


class CustomValueExample(models.Model):

    class StrPropsEnum(Enum):

        STR1 = StrProps('str1')
        STR2 = StrProps('str2')
        STR3 = StrProps('str3')

    str_props = EnumField(StrPropsEnum, primitive=str)
