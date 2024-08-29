"""
Support for symmetrical property enumeration types derived from Django choice
types. These choices types are drop in replacements for the Django
IntegerChoices and TextChoices.
"""

import enum

from django import VERSION as django_version
from django.db.models import Choices
from django.db.models import IntegerChoices as DjangoIntegerChoices
from django.db.models import TextChoices as DjangoTextChoices
from django.db.models import enums as model_enums

from django_enum.utils import choices, names

ChoicesType = (
    model_enums.ChoicesType
    if django_version[0:2] >= (5, 0)
    else model_enums.ChoicesMeta
)

DEFAULT_BOUNDARY = getattr(enum, "KEEP", None)


try:
    from enum_properties import DecomposeMixin, EnumPropertiesMeta, SymmetricMixin

    class DjangoEnumPropertiesMeta(EnumPropertiesMeta, ChoicesType):  # type: ignore
        """
        A composite meta class that combines Django's Choices metaclass with
        enum-properties metaclass. This metaclass will add Django's expected
        choices attribute and label properties to enumerations and
        enum-properties' generic property support.
        """

        @property
        def names(self):
            """
            For some eccentric enums list(Enum) is empty, so we override names
            if empty
            """
            return super().names or names(self, override=True)

        @property
        def choices(self):
            """
            For some eccentric enums list(Enum) is empty, so we override
            choices if empty
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

except (ImportError, ModuleNotFoundError):
    # 3.11 - extend from Enum so base type check does not throw type error
    class MissingEnumProperties(enum.Enum):
        """Throw error if choice types are used without enum-properties"""

        def __init__(self, *args, **kwargs):
            raise ImportError(
                f"{self.__class__.__name__} requires enum-properties to be "
                f"installed."
            )

    DjangoSymmetricMixin = MissingEnumProperties  # type: ignore

    class DjangoEnumPropertiesMeta(ChoicesType):  # type: ignore
        """
        Throw error if metaclass is used without enum-properties

        Needs to be strict subclass of same metaclass as Enum to make it to
        the ImportError.
        """

        def __init__(cls, *args, **kwargs):
            raise ImportError(
                f"{cls.__class__.__name__} requires enum-properties to be "
                f"installed."
            )

    class TextChoices(DjangoSymmetricMixin, str, Choices):  # type: ignore
        """Raises ImportError on class definition"""

    class IntegerChoices(DjangoSymmetricMixin, int, Choices):  # type: ignore
        """Raises ImportError on class definition"""

    class FloatChoices(DjangoSymmetricMixin, float, Choices):  # type: ignore
        """Raises ImportError on class definition"""

    class FlagChoices(DjangoSymmetricMixin, enum.IntFlag, Choices):  # type: ignore
        """Raises ImportError on class definition"""
