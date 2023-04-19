"""Utility routines for django_enum."""

from enum import Enum
from typing import Any, List, Optional, Tuple, Type

__all__ = [
    'choices',
    'names',
    'labels',
    'values',
    'determine_primitive',
    'SUPPORTED_PRIMITIVES'
]


SUPPORTED_PRIMITIVES = {int, str, float}


def choices(enum_cls: Optional[Type[Enum]]) -> List[Tuple[Any, str]]:
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


def names(enum_cls: Optional[Type[Enum]]) -> List[Any]:
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


def labels(enum_cls: Optional[Type[Enum]]) -> List[Any]:
    """
    Return a list of labels to use for the enumeration type. See choices.

    This is used for compat with enums that do not inherit from Django's
    Choices type.

    :param enum_cls: The enumeration type
    :return: A list of labels
    """
    return getattr(
        enum_cls,
        'labels',
        [label for _, label in choices(enum_cls)]
    )


def values(enum_cls: Optional[Type[Enum]]) -> List[Any]:
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


def determine_primitive(enum: Type[Enum]) -> Optional[Type]:
    """
    Determine the python type most appropriate to represent all values of the
    enumeration class. The primitive type determination algorithm is thus:

        * Determine the types of all the values in the enumeration
        * Determine the first supported primitive type in the enumeration class
          inheritance tree
        * If there is only one value type, use its type as the primitive
        * If there are multiple value types and they are all subclasses of
          the class primitive type, use the class primitive type. If there is
          no class primitive type use the first supported primitive type that
          all values are symmetrically coercible to. If there is no such type,
          return None

    By definition all values of the enumeration with the exception of None
    may be coerced to the primitive type and vice-versa.

    :param enum: The enumeration class to determine the primitive type for
    :return: A python type or None if no primitive type could be determined
    """
    primitive = None
    if enum:
        for prim in enum.__mro__:
            if primitive:
                break  # type: ignore
            for supported in SUPPORTED_PRIMITIVES:
                if issubclass(prim, supported):
                    primitive = supported
                    break
        value_types = set()
        for value in values(enum):
            if value is not None:
                value_types.add(type(value))

        if len(value_types) > 1 and primitive is None:
            for candidate in SUPPORTED_PRIMITIVES:
                works = True
                for value in values(enum):
                    if value is None:
                        continue
                    try:
                        # test symmetric coercibility
                        works &= type(value)(candidate(value)) == value
                    except (TypeError, ValueError):
                        works = False
                if works:
                    return candidate
        elif value_types:
            return list(value_types).pop()
    return primitive
