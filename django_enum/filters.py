"""Support for django-filter"""

from typing import Tuple, Type

from django.db.models import Field as ModelField
from django.forms.fields import Field as FormField
from django_enum.fields import EnumMixin
from django_enum.forms import EnumChoiceField


try:
    from django_filters import ChoiceFilter, Filter, filterset

    class EnumFilter(ChoiceFilter):
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
        """
        field_class: FormField = EnumChoiceField

        def __init__(self, *, enum, **kwargs):
            self.enum = enum
            super().__init__(
                enum=enum,
                choices=kwargs.pop('choices', self.enum.choices),
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
            if isinstance(field, EnumMixin) and getattr(field, 'enum', None):
                return EnumFilter, {'enum': field.enum}
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
