"""Support for django-filter"""

from typing import Tuple, Type

from django.db.models import Field as ModelField
from django.forms.fields import Field as FormField
from django_enum.choices import choices
from django_enum.forms import EnumChoiceField

try:
    from django_filters import Filter, TypedChoiceFilter, filterset

    class EnumFilter(TypedChoiceFilter):
        """
        Use this filter class instead of ``ChoiceFilter`` to get filters to
        accept Enum labels and symmetric properties.

        For example if we have an enumeration field defined with the following
        Enum:

        .. code-block::

            class Color(TextChoices, s('rgb'), s('hex', case_fold=True)):
                RED = 'R', 'Red', (1, 0, 0), 'ff0000'
                GREEN = 'G', 'Green', (0, 1, 0), '00ff00'
                BLUE = 'B', 'Blue', (0, 0, 1), '0000ff'

            color = EnumField(Color)

        The default ``ChoiceFilter`` will only work with the enumeration
        values: ?color=R, ?color=G, ?color=B. ``EnumFilter`` will accept query
        parameter values from any of the symmetric properties: ?color=Red,
        ?color=ff0000, etc...

        :param enum: The class of the enumeration containing the values to
            filter on
        :param strict: If False (default), values not in the enumeration will
            be searchable.
        :param kwargs: Any additional arguments for base classes
        """
        field_class: FormField = EnumChoiceField

        def __init__(self, *, enum, strict=False, **kwargs):
            self.enum = enum
            super().__init__(
                enum=enum,
                choices=kwargs.pop('choices', choices(self.enum)),
                strict=strict,
                **kwargs
            )

    class FilterSet(filterset.FilterSet):
        """
        Use this class instead of django-filter's ``FilterSet`` class to
        automatically set all ``EnumField`` filters to ``EnumFilter`` by
        default instead of ``ChoiceFilter``.
        """
        @classmethod
        def filter_for_lookup(
                cls,
                field: ModelField,
                lookup_type: str
        ) -> Tuple[Type[Filter], dict]:
            """For EnumFields use the EnumFilter class by default"""
            if hasattr(field, 'enum'):
                return EnumFilter, {
                    'enum': field.enum,
                    'strict': getattr(field, 'strict', False)
                }
            return super().filter_for_lookup(field, lookup_type)


except (ImportError, ModuleNotFoundError):

    class _MissingDjangoFilters:
        """Throw error if filter support is used without django-filter"""

        def __init__(self, *args, **kwargs):
            raise ImportError(
                f'{self.__class__.__name__} requires django-filter to be '
                f'installed.'
            )

    EnumFilter = _MissingDjangoFilters  # type: ignore
    FilterSet = _MissingDjangoFilters  # type: ignore
