"""
Support for :doc:`django-filter <django-filter:index>`.
"""

import typing as t
from enum import Enum, Flag

from django.db.models import Field as ModelField
from django.db.models import Q
from django_filters import filterset
from django_filters.filters import Filter, TypedChoiceFilter, TypedMultipleChoiceFilter
from django_filters.utils import try_dbfield

from django_enum.fields import EnumField, FlagField
from django_enum.forms import EnumChoiceField, EnumFlagField, EnumMultipleChoiceField
from django_enum.utils import choices

__all__ = [
    "EnumFilter",
    "MultipleEnumFilter",
    "EnumFlagFilter",
    "FilterSet",
]


class EnumFilter(TypedChoiceFilter):
    """
    Use this filter class instead of :class:`~django_filters.filters.ChoiceFilter`
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

    The default :class:`~django_filters.filters.ChoiceFilter` will only work with
    the enumeration values: ?color=R, ?color=G, ?color=B. ``EnumFilter`` will accept
    query parameter values from any of the symmetric properties: ?color=Red,
    ?color=ff0000, etc...

    :param enum: The class of the enumeration containing the values to
        filter on
    :param strict: If False (default), values not in the enumeration will
        be searchable.
    :param kwargs: Any additional arguments from the base classes
        (:class:`~django_filters.filters.TypedChoiceFilter`)
    """

    enum: t.Type[Enum]
    field_class = EnumChoiceField

    def __init__(self, *, enum: t.Type[Enum], **kwargs):
        self.enum = enum
        super().__init__(
            enum=enum,
            choices=kwargs.pop("choices", choices(self.enum)),
            **kwargs,
        )


class MultipleEnumFilter(TypedMultipleChoiceFilter):
    """
    Use this filter class instead of
    :class:`~django_filters.filters.MultipleChoiceFilter` to get filters to accept
    multiple :class:`~enum.Enum` labels and symmetric properties.

    :param enum: The class of the enumeration containing the values to
        filter on
    :param strict: If False (default), values not in the enumeration will
        be searchable.
    :param conjoined: If True require all values to be present, if False require any
    :param kwargs: Any additional arguments from base classes,
        (:class:`~django_filters.filters.TypedMultipleChoiceFilter`)
    """

    enum: t.Type[Enum]
    field_class = EnumMultipleChoiceField

    def __init__(
        self,
        *,
        enum: t.Type[Enum],
        conjoined: bool = False,
        **kwargs,
    ):
        self.enum = enum
        super().__init__(
            enum=enum,
            choices=kwargs.pop("choices", choices(self.enum)),
            conjoined=conjoined,
            **kwargs,
        )


class EnumFlagFilter(TypedMultipleChoiceFilter):
    """
    Use this filter class instead of
    :class:`~django_filters.filters.MultipleChoiceFilter` to get filters to accept
    multiple :class:`~enum.Enum` labels and symmetric properties.

    :param enum: The class of the enumeration containing the values to
        filter on
    :param strict: If False (default), values not in the enumeration will
        be searchable.
    :param conjoined: If True use :ref:`has_all` lookup, otherwise use :ref:`has_any`
        (default)
    :param kwargs: Any additional arguments from base classes,
        (:class:`~django_filters.filters.TypedMultipleChoiceFilter`)
    """

    enum: t.Type[Flag]
    field_class = EnumFlagField

    def __init__(
        self,
        *,
        enum: t.Type[Flag],
        conjoined: bool = False,
        strict: bool = False,
        **kwargs,
    ):
        self.enum = enum
        self.lookup_expr = "has_all" if conjoined else "has_any"
        super().__init__(
            enum=enum,
            choices=kwargs.pop("choices", choices(self.enum)),
            strict=strict,
            conjoined=conjoined,
            **kwargs,
        )

    def filter(self, qs, value):
        if value == self.null_value:
            value = None

        if not value:
            return qs

        if self.is_noop(qs, value):
            return qs

        qs = self.get_method(qs)(Q(**self.get_filter_predicate(value)))
        return qs.distinct() if self.distinct else qs


class FilterSet(filterset.FilterSet):
    """
    Use this class instead of the :doc:`django-filter <django-filter:index>`
    :class:`~django_filters.filterset.FilterSet` to automatically set all
    :class:`~django_enum.fields.EnumField` filters to
    :class:`~django_enum.filters.EnumFilter` by default instead of
    :class:`~django_filters.filters.ChoiceFilter`.
    """

    @staticmethod
    def enum_extra(f: EnumField) -> t.Dict[str, t.Any]:
        return {"enum": f.enum, "choices": f.choices}

    FILTER_DEFAULTS = {
        **{
            FlagField: {
                "filter_class": EnumFlagFilter,
                "extra": enum_extra,
            },
            EnumField: {
                "filter_class": EnumFilter,
                "extra": enum_extra,
            },
        },
        **filterset.FilterSet.FILTER_DEFAULTS,
    }

    @classmethod
    def filter_for_lookup(
        cls, field: ModelField, lookup_type: str
    ) -> t.Tuple[t.Optional[t.Type[Filter]], t.Dict[str, t.Any]]:
        """For EnumFields use the EnumFilter class by default"""
        if isinstance(field, EnumField):
            data = (
                try_dbfield(
                    {
                        **cls.FILTER_DEFAULTS,
                        **(
                            getattr(getattr(cls, "_meta", None), "filter_overrides", {})
                        ),
                    }.get,
                    field.__class__,
                )
                or {}
            )
            return (
                data["filter_class"],
                {
                    **cls.enum_extra(field),
                    **data.get("extra", lambda f: {})(field),
                },
            )
        return super().filter_for_lookup(field, lookup_type)
