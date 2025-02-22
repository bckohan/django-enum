"""Utility routines for django_enum."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntFlag
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from typing_extensions import get_args

__all__ = [
    "choices",
    "names",
    "labels",
    "values",
    "determine_primitive",
    "with_typehint",
    "SupportedPrimitive",
    "decimal_params",
    "get_set_bits",
]


T = TypeVar("T")

SupportedPrimitive = Union[
    int,
    str,
    float,
    # bytes,
    date,
    datetime,
    time,
    timedelta,
    Decimal,
]


def with_typehint(baseclass: Type[T]) -> Type[T]:
    """
    Change inheritance to add Field type hints when type checking is running.
    This is just more simple than defining a Protocol - revisit if Django
    provides Field protocol - should also just be a way to create a Protocol
    from a class?

    This is icky but it works - revisit in future.
    """
    if TYPE_CHECKING:
        return baseclass  # pragma: no cover
    return object  # type: ignore


def choices(
    enum_cls: Optional[Type[Enum]], override: bool = False
) -> List[Tuple[Any, str]]:
    """
    Get the Django choices for an enumeration type. If the enum type has a
    choices attribute, it will be used. Otherwise, the choices will be derived
    from value, label pairs if the enumeration type has a label attribute, or
    the name attribute if it does not.

    This is used for compat with enums that do not inherit from Django's
    Choices type.

    :param enum_cls: The enumeration type
    :param override: Do not defer to choices attribute on the class if True
    :return: A list of (value, label) pairs
    """
    return (
        (getattr(enum_cls, "choices", []) if not override else [])
        or (
            [
                *(
                    [(None, enum_cls.__empty__)]
                    if hasattr(enum_cls, "__empty__")
                    else []
                ),
                *[
                    (member.value, getattr(member, "label", getattr(member, "name")))
                    for member in list(enum_cls) or enum_cls.__members__.values()
                ],
            ]
        )
        if enum_cls
        else []
    )


def names(enum_cls: Optional[Type[Enum]], override: bool = False) -> List[Any]:
    """
    Return a list of names to use for the enumeration type. This is used
    for compat with enums that do not inherit from Django's Choices type.

    :param enum_cls: The enumeration type
    :param override: Do not defer to names attribute on the class if True
    :return: A list of labels
    """
    return (
        (getattr(enum_cls, "names", []) if not override else [])
        or (
            [
                *(["__empty__"] if hasattr(enum_cls, "__empty__") else []),
                *[
                    member.name
                    for member in list(enum_cls) or enum_cls.__members__.values()
                ],
            ]
        )
        if enum_cls
        else []
    )


def labels(enum_cls: Optional[Type[Enum]]) -> List[Any]:
    """
    Return a list of labels to use for the enumeration type. See choices.

    This is used for compat with enums that do not inherit from Django's
    Choices type.

    :param enum_cls: The enumeration type
    :return: A list of labels
    """
    return getattr(enum_cls, "labels", [label for _, label in choices(enum_cls)])


def values(enum_cls: Optional[Type[Enum]]) -> List[Any]:
    """
    Return a list of the values of an enumeration type.

    This is used for compat with enums that do not inherit from Django's
    Choices type.

    :param enum_cls: The enumeration type
    :return: A list of values
    """
    return getattr(enum_cls, "values", [value for value, _ in choices(enum_cls)])


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
    for prim in enum.__mro__:
        if issubclass(prim, get_args(SupportedPrimitive)):
            primitive = prim
            break
    value_types = set()
    for value in values(enum):
        if value is not None:
            value_types.add(type(value))

    if len(value_types) > 1 and primitive is None:
        for candidate in get_args(SupportedPrimitive):
            works = True
            for value in values(enum):
                if value is None:
                    continue
                try:
                    # test symmetric coercibility
                    works &= type(value)(candidate(value)) == value
                except Exception:
                    works = False
            if works:
                return candidate
    elif value_types:
        return list(value_types).pop()
    return primitive


def decimal_params(
    enum: Optional[Type[Enum]],
    decimal_places: Optional[int] = None,
    max_digits: Optional[int] = None,
) -> Dict[str, int]:
    """
    Determine the maximum number of digits and decimal places required to
    represent all values of the enumeration class.

    :param enum: The enumeration class to determine the decimal parameters for
    :param decimal_places: Use this value for decimal_places rather than
        the computed value
    :param max_digits: Use this value for max_digits rather than the computed
        value
    :return: A tuple of (max_digits, decimal_places)
    """
    decimal_places = decimal_places or max(
        [0]
        + [len(str(value).split(".")[1]) for value in values(enum) if "." in str(value)]
    )
    max_digits = max_digits or (
        decimal_places
        + max(
            [0] + [len(str(value).split(".", maxsplit=1)[0]) for value in values(enum)]
        )
    )
    return {"max_digits": max_digits, "decimal_places": decimal_places}


def get_set_bits(flag: Union[int, IntFlag]) -> List[int]:
    """
    Return the indices of the bits set in the flag.

    :param flag: The flag to get the set bits for, value must be an int.
    :return: A list of indices of the set bits
    """
    return [i for i in range(flag.bit_length()) if flag & (1 << i)]
