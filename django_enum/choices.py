"""
Support for symmetrical property enumeration types derived from Django choice
types. These choices types are drop in replacements for the Django
IntegerChoices and TextChoices.
"""
import enum
from typing import Any, List, Optional, Tuple, Type

from django.db.models import Choices
from django.db.models import IntegerChoices as DjangoIntegerChoices
from django.db.models import TextChoices as DjangoTextChoices
from django.db.models.enums import ChoicesMeta


DEFAULT_BOUNDARY = getattr(enum, 'KEEP', None)


def choices(enum_cls: Optional[Type[enum.Enum]]) -> List[Tuple[Any, str]]:
    """
    Get the Django choices for an enumeration type. If the enum type has a
    choices attribute, it will be used. Otherwise, the choices will be derived
    from value, label pairs if the enumeration type has a label attribute, or
    the name attribute if it does not.

    This is used for compat with enums that do not inherit from Django's
    Choices type.

    :param enum_cls: The enumeration type
    :return: A list of (value, label) pairs
    """
    return getattr(
        enum_cls,
        'choices', [
            *(
                [(None, enum_cls.__empty__)]
                if hasattr(enum_cls, '__empty__') else []
            ),
            *[
                (
                    member.value,
                    getattr(member, 'label', getattr(member, 'name'))
                )
                for member in enum_cls
            ]
        ]
    ) if enum_cls else []


def names(enum_cls: Optional[Type[enum.Enum]]) -> List[Any]:
    """
    Return a list of names to use for the enumeration type. This is used
    for compat with enums that do not inherit from Django's Choices type.

    :param enum_cls: The enumeration type
    :return: A list of labels
    """
    return getattr(
        enum_cls,
        'names', [
            *(['__empty__'] if hasattr(enum_cls, '__empty__') else []),
            *[member.name for member in enum_cls]
        ]
    ) if enum_cls else []


def labels(enum_cls: Optional[Type[enum.Enum]]) -> List[Any]:
    """
    Return a list of labels to use for the enumeration type. See choices.

    This is used for compat with enums that do not inherit from Django's
    Choices type.

    :param enum: The enumeration type
    :return: A list of labels
    """
    return getattr(
        enum_cls,
        'labels',
        [label for _, label in choices(enum_cls)]
    )


def values(enum_cls: Optional[Type[enum.Enum]]) -> List[Any]:
    """
    Return a list of the values of an enumeration type.

    This is used for compat with enums that do not inherit from Django's
    Choices type.

    :param enum_cls: The enumeration type
    :return: A list of values
    """
    return getattr(
        enum_cls,
        'values',
        [value for value, _ in choices(enum_cls)]
    )


try:
    from enum_properties import (
        DecomposeMixin,
        EnumPropertiesMeta,
        SymmetricMixin,
    )


    class DjangoEnumPropertiesMeta(EnumPropertiesMeta, ChoicesMeta):
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


    class TextChoices(
        DjangoSymmetricMixin,
        DjangoTextChoices,
        metaclass=DjangoEnumPropertiesMeta
    ):
        """
        A character enumeration type that extends Django's TextChoices and
        accepts enum-properties property lists.
        """


    class IntegerChoices(
        DjangoSymmetricMixin,
        DjangoIntegerChoices,
        metaclass=DjangoEnumPropertiesMeta
    ):
        """
        An integer enumeration type that extends Django's IntegerChoices and
        accepts enum-properties property lists.
        """


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

    # mult inheritance type hint bug
    class FlagChoices(  # type: ignore
        DecomposeMixin,
        DjangoSymmetricMixin,
        enum.IntFlag,
        Choices,
        metaclass=DjangoEnumPropertiesMeta,
        # default boundary argument gets lost in the inheritance when choices
        # is included if it is not explicitly specified
        **(
            {'boundary': DEFAULT_BOUNDARY}
            if DEFAULT_BOUNDARY is not None
            else {}
        )
    ):
        """
        An integer flag enumeration type that accepts enum-properties property
        lists.
        """


except (ImportError, ModuleNotFoundError):

    # 3.11 - extend from Enum so base type check does not throw type error
    class MissingEnumProperties(enum.Enum):
        """Throw error if choice types are used without enum-properties"""

        def __init__(self, *args, **kwargs):  # pylint: disable=W0231
            raise ImportError(
                f'{self.__class__.__name__} requires enum-properties to be '
                f'installed.'
            )

    DjangoSymmetricMixin = MissingEnumProperties  # type: ignore


    class DjangoEnumPropertiesMeta(ChoicesMeta):  # type: ignore
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

    class FlagChoices(  # type: ignore
        DjangoSymmetricMixin,
        enum.IntFlag,
        Choices
    ):
        """Raises ImportError on class definition"""
