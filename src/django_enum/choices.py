"""
Support for symmetrical property enumeration types derived from Django choice
types. These choices types are drop in replacements for the Django
IntegerChoices and TextChoices.
"""

import enum
import typing as t

from django import VERSION as django_version
from django.db.models import Choices
from django.db.models import IntegerChoices as DjangoIntegerChoices
from django.db.models import TextChoices as DjangoTextChoices
from django.db.models import enums as model_enums
from enum_properties import DecomposeMixin, EnumPropertiesMeta, SymmetricMixin

from django_enum.utils import choices, names

ChoicesType = (
    model_enums.ChoicesType
    if django_version[0:2] >= (5, 0)
    else model_enums.ChoicesMeta
)

DEFAULT_BOUNDARY = getattr(enum, "KEEP", None)


class DjangoEnumPropertiesMeta(EnumPropertiesMeta, ChoicesType):  # type: ignore
    """
    A composite meta class that combines Django's Choices metaclass with
    enum-properties metaclass. This metaclass will add Django's expected
    choices attribute and label properties to enumerations and
    enum-properties' generic property support.
    """

    def __new__(mcs, classname, bases, classdict, **kwargs):
        cls = super().__new__(mcs, classname, bases, classdict, **kwargs)
        # choices does not allow duplicates, but base class construction breaks
        # this member, so we alias it here to stay compatible with enum-properties
        # interface
        # TODO - is this a fixable bug in ChoicesType?
        cls._member_names_ = (
            list(classdict._member_names.keys())
            if isinstance(classdict._member_names, dict)  # changes based on py ver
            else classdict._member_names
        )
        cls.__first_class_members__ = cls._member_names_
        return cls

    @property
    def names(self) -> t.List[str]:
        """
        For some eccentric enums list(Enum) is empty, so we override names
        if empty.

        :returns: list of enum value names
        """
        return super().names or names(self, override=True)

    @property
    def choices(self) -> t.List[t.Tuple[t.Any, str]]:
        """
        For some eccentric enums list(Enum) is empty, so we override
        choices if empty

        :returns: list of enum value choices
        """
        return super().choices or choices(self, override=True)


class DjangoSymmetricMixin(SymmetricMixin):
    """
    An enumeration mixin that makes Django's Choices type label field
    symmetric.
    """

    _symmetric_builtins_ = ["name", "label"]


class TextChoices(
    DjangoSymmetricMixin, DjangoTextChoices, metaclass=DjangoEnumPropertiesMeta
):
    """
    A character enumeration type that extends Django's TextChoices and
    accepts enum-properties property lists.
    """

    def __hash__(self):
        return DjangoTextChoices.__hash__(self)


class IntegerChoices(
    DjangoSymmetricMixin, DjangoIntegerChoices, metaclass=DjangoEnumPropertiesMeta
):
    """
    An integer enumeration type that extends Django's IntegerChoices and
    accepts enum-properties property lists.
    """

    def __hash__(self):
        return DjangoIntegerChoices.__hash__(self)


class FloatChoices(
    DjangoSymmetricMixin, float, Choices, metaclass=DjangoEnumPropertiesMeta
):
    """
    A floating point enumeration type that accepts enum-properties
    property lists.
    """

    def __hash__(self):
        return float.__hash__(self)

    def __str__(self):
        return str(self.value)


# mult inheritance type hint bug
class FlagChoices(  # type: ignore
    DecomposeMixin,
    DjangoSymmetricMixin,
    enum.IntFlag,
    Choices,
    metaclass=DjangoEnumPropertiesMeta,
    # default boundary argument gets lost in the inheritance when choices
    # is included if it is not explicitly specified
    **({"boundary": DEFAULT_BOUNDARY} if DEFAULT_BOUNDARY is not None else {}),
):
    """
    An integer flag enumeration type that accepts enum-properties property
    lists.
    """

    def __hash__(self):
        return enum.IntFlag.__hash__(self)
