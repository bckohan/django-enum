"""
Support for :doc:`django-filter <django-filter:index>`.
"""

import typing as t
from enum import Enum

from django.db.models import Field as ModelField
from django_filters import (
    Filter,
    TypedChoiceFilter,
    TypedMultipleChoiceFilter,
    filterset,
)

from django_enum.fields import EnumField
from django_enum.forms import EnumChoiceField, EnumMultipleChoiceField
from django_enum.utils import choices

__all__ = [
    "EnumFilter",
    "MultipleEnumFilter",
    "FilterSet",
]


class EnumFilter(TypedChoiceFilter):
    """
    Use this filter class instead of :ref:`ChoiceFilter <django-filter:choice-filter>`
    to get filters to accept :class:`~enum.Enum` labels and symmetric properties.

    For example if we have an enumeration field defined with the following
    Enum:

    .. code-block:: python

        class Color(TextChoices):

            rgb: Annotated[Tuple[int, int, int], Symmetric()]
            hex: Annotated[str, Symmetric(case_fold=True)]

            RED   = 'R', 'Red',   (1, 0, 0), 'ff0000'
            GREEN = 'G', 'Green', (0, 1, 0), '00ff00'
            BLUE  = 'B', 'Blue',  (0, 0, 1), '0000ff'

        color = EnumField(Color)

    The default :ref:`ChoiceFilter <django-filter:choice-filter>` will only work with
    the enumeration values: ?color=R, ?color=G, ?color=B. ``EnumFilter`` will accept
    query parameter values from any of the symmetric properties: ?color=Red,
    ?color=ff0000, etc...

    :param enum: The class of the enumeration containing the values to
        filter on
    :param strict: If False (default), values not in the enumeration will
        be searchable.
    :param kwargs: Any additional arguments for base classes
    """

    enum: t.Type[Enum]
    field_class = EnumChoiceField

    def __init__(self, *, enum: t.Type[Enum], strict: bool = False, **kwargs):
        self.enum = enum
        super().__init__(
            enum=enum,
            choices=kwargs.pop("choices", choices(self.enum)),
            strict=strict,
            **kwargs,
        )


class MultipleEnumFilter(TypedMultipleChoiceFilter):
    """
    Use this filter class instead of
    :ref:`MultipleChoiceFilter <django-filter:multiple-choice-filter>`
    to get filters to accept multiple :class:`~enum.Enum` labels and symmetric
    properties.

    :param enum: The class of the enumeration containing the values to
        filter on
    :param strict: If False (default), values not in the enumeration will
        be searchable.
    :param kwargs: Any additional arguments for base classes
    """

    enum: t.Type[Enum]
    field_class = EnumMultipleChoiceField

    def __init__(self, *, enum: t.Type[Enum], strict: bool = False, **kwargs):
        self.enum = enum
        super().__init__(
            enum=enum,
            choices=kwargs.pop("choices", choices(self.enum)),
            strict=strict,
            **kwargs,
        )


class FilterSet(filterset.FilterSet):
    """
    Use this class instead of the :doc:`django-filter <django-filter:index>`
    :doc:`FilterSet <django-filter:ref/filterset>` class to automatically set all
    :class:`~django_enum.fields.EnumField` filters to
    :class:`~django_enum.filters.EnumFilter` by default instead of
    :ref:`ChoiceFilter <django-filter:choice-filter>`.
    """

    @classmethod
    def filter_for_lookup(
        cls, field: ModelField, lookup_type: str
    ) -> t.Tuple[t.Optional[t.Type[Filter]], t.Dict[str, t.Any]]:
        """For EnumFields use the EnumFilter class by default"""
        if isinstance(field, EnumField):
            return EnumFilter, {
                "enum": field.enum,
                "strict": getattr(field, "strict", False),
            }
        return super().filter_for_lookup(field, lookup_type)
