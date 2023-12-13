"""
Support for symmetrical property enumeration types derived from Django choice
types. These choices types are drop in replacements for the Django
IntegerChoices and TextChoices.
"""
from enum import Enum
from typing import Any, List, Optional, Tuple, Type

from django.db.models import Choices
from django.db.models import IntegerChoices as DjangoIntegerChoices
from django.db.models import TextChoices as DjangoTextChoices

try:
    from django.db.models.enums import ChoicesType
except ImportError:  # pragma: no cover
    from django.db.models.enums import ChoicesMeta as ChoicesType


def choices(enum: Optional[Type[Enum]]) -> List[Tuple[Any, str]]:
    """
    Get the Django choices for an enumeration type. If the enum type has a
    choices attribute, it will be used. Otherwise, the choices will be derived
    from value, label pairs if the enumeration type has a label attribute, or
    the name attribute if it does not.

    This is used for compat with enums that do not inherit from Django's
    Choices type.

    :param enum: The enumeration type
    :return: A list of (value, label) pairs
    """
    return getattr(
        enum,
        'choices', [
            *([(None, enum.__empty__)] if hasattr(enum, '__empty__') else []),
            *[
                (
                    member.value,
                    getattr(member, 'label', getattr(member, 'name'))
                )
                for member in enum
            ]
        ]
    ) if enum else []


def names(enum: Optional[Type[Enum]]) -> List[Any]:
    """
    Return a list of names to use for the enumeration type. This is used
    for compat with enums that do not inherit from Django's Choices type.

    :param enum: The enumeration type
    :return: A list of labels
    """
    return getattr(
        enum,
        'names', [
            *(['__empty__'] if hasattr(enum, '__empty__') else []),
            *[member.name for member in enum]
        ]
    ) if enum else []


def labels(enum: Optional[Type[Enum]]) -> List[Any]:
    """
    Return a list of labels to use for the enumeration type. See choices.

    This is used for compat with enums that do not inherit from Django's
    Choices type.

    :param enum: The enumeration type
    :return: A list of labels
    """
    return getattr(enum, 'labels', [label for _, label in choices(enum)])


def values(enum: Optional[Type[Enum]]) -> List[Any]:
    """
    Return a list of the values of an enumeration type.

    This is used for compat with enums that do not inherit from Django's
    Choices type.

    :param enum: The enumeration type
    :return: A list of values
    """
    return getattr(enum, 'values', [value for value, _ in choices(enum)])


try:
    from enum_properties import EnumPropertiesMeta, SymmetricMixin


    class DjangoEnumPropertiesMeta(EnumPropertiesMeta, ChoicesType):
        """
        A composite meta class that combines Django's Choices metaclass with
        enum-properties metaclass. This metaclass will add Django's expected
        choices attribute and label properties to enumerations and
        enum-properties' generic property support.
        """


    class DjangoSymmetricMixin(SymmetricMixin):
        """
        An enumeration mixin that makes Django's Choices type label field
        symmetric.
        """
        _symmetric_builtins_ = ['name', 'label']


    class TextChoices(  # pylint: disable=too-many-ancestors
        DjangoSymmetricMixin,
        DjangoTextChoices,
        metaclass=DjangoEnumPropertiesMeta
    ):
        """
        A character enumeration type that extends Django's TextChoices and
        accepts enum-properties property lists.
        """

        def __hash__(self):
            return DjangoTextChoices.__hash__(self)


    class IntegerChoices(  # pylint: disable=too-many-ancestors
        DjangoSymmetricMixin,
        DjangoIntegerChoices,
        metaclass=DjangoEnumPropertiesMeta
    ):
        """
        An integer enumeration type that extends Django's IntegerChoices and
        accepts enum-properties property lists.
        """

        def __hash__(self):
            return DjangoIntegerChoices.__hash__(self)


    class FloatChoices(
        DjangoSymmetricMixin,
        float,
        Choices,
        metaclass=DjangoEnumPropertiesMeta
    ):
        """
        A floating point enumeration type that accepts enum-properties
        property lists.
        """

        def __hash__(self):
            return float.__hash__(self)

        def __str__(self):
            return str(self.value)


except (ImportError, ModuleNotFoundError):

    # 3.11 - extend from Enum so base type check does not throw type error
    class MissingEnumProperties(Enum):
        """Throw error if choice types are used without enum-properties"""

        def __init__(self, *args, **kwargs):  # pylint: disable=W0231
            raise ImportError(
                f'{self.__class__.__name__} requires enum-properties to be '
                f'installed.'
            )

    DjangoSymmetricMixin = MissingEnumProperties  # type: ignore


    class DjangoEnumPropertiesMeta(ChoicesType):  # type: ignore
        """
        Throw error if metaclass is used without enum-properties

        Needs to be strict subclass of same metaclass as Enum to make it to
        the ImportError.
        """
        def __init__(cls, *args, **kwargs):  # pylint: disable=W0231
            raise ImportError(
                f'{cls.__class__.__name__} requires enum-properties to be '
                f'installed.'
            )

    class TextChoices(  # type: ignore
        DjangoSymmetricMixin,
        str,
        Choices
    ):
        """Raises ImportError on class definition"""

    class IntegerChoices(  # type: ignore
        DjangoSymmetricMixin,
        int,
        Choices
    ):
        """Raises ImportError on class definition"""

    class FloatChoices(  # type: ignore
        DjangoSymmetricMixin,
        float,
        Choices
    ):
        """Raises ImportError on class definition"""
