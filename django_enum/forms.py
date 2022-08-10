"""Enumeration support for django model forms"""
from typing import Any, Iterable, List, Tuple, Type, Union

from django.core.exceptions import ValidationError
from django.db.models import Choices
from django.forms.fields import ChoiceField
from django.forms.widgets import Select

# pylint: disable=R0801

__all__ = ['NonStrictSelect', 'EnumChoiceField']


class _Unspecified:
    """
    Marker used by EnumChoiceField to determine if empty_value
    was overridden
    """


class NonStrictSelect(Select):
    """
    A Select widget for non-strict EnumChoiceFields that includes any existing
    non-conforming value as a choice option.
    """

    choices: Iterable[Tuple[Any, str]]

    def render(self, *args, **kwargs):
        """
        Before rendering if we're a non-strict field and our value is not
        one of our choices, we add it as an option.
        """

        value: Any = getattr(kwargs.get('value'), 'value', kwargs.get('value'))
        if (
            value not in EnumChoiceField.empty_values
            and value not in (
                choice[0] for choice in self.choices
            )
        ):
            self.choices = list(self.choices) + [(value, str(value))]
        return super().render(*args, **kwargs)


class EnumChoiceField(ChoiceField):
    """
    The default ``ChoiceField`` will only accept the base enumeration values.
    Use this field on forms to accept any value mappable to an enumeration
    including any labels or symmetric properties.

    :param enum: The Enumeration type
    :param empty_value: Allow users to define what empty is because some
        enumeration types might use an empty value (i.e. empty string) as an
        enumeration value. This value will be returned when any "empty" value
        is encountered. If unspecified the default empty value of '' is
        returned.
    :param strict: If False, values not included in the enumeration list, but
        of the same primitive type are acceptable.
    :param choices: Override choices, otherwise enumeration choices attribute
        will be used.
    :param kwargs: Any additional parameters to pass to ChoiceField base class.
    """

    enum: Type[Choices]
    strict: bool = True
    empty_value: Any = ''
    empty_values: List[Any]

    def __init__(
            self,
            enum: Type[Choices],
            *,
            empty_value: Any = _Unspecified,
            strict: bool = strict,
            choices: Iterable[Tuple[Any, str]] = (),
            **kwargs
    ):
        self.enum = enum
        self.strict = strict
        if not self.strict:
            kwargs.setdefault('widget', NonStrictSelect)

        super().__init__(
            choices=choices or getattr(self.enum, 'choices', ()),
            **kwargs
        )

        if empty_value is not _Unspecified:
            self.empty_values.insert(0, empty_value)
            self.empty_value = empty_value

        # remove any of our valid enumeration values or symmetric properties
        # from our empty value list if there exists an equivalency
        for empty in self.empty_values:
            for enum_val in self.enum:
                if empty == enum_val:
                    # copy the list instead of modifying the class's
                    self.empty_values = [
                        empty for empty in self.empty_values
                        if empty != enum_val
                    ]
                    if empty == self.empty_value:
                        raise ValueError(
                            f'Enumeration value {repr(enum_val)} is equivalent'
                            f' to {self.empty_value}, you must specify a '
                            f'non-conflicting empty_value.'
                        )

    def _coerce_to_value_type(self, value: Any) -> Any:
        """Coerce the value to the enumerations value type"""
        return type(self.enum.values[0])(value)

    def _coerce(self, value: Any) -> Union[Choices, Any]:
        """
        Attempt conversion of value to an enumeration value and return it
        if successful.

        :param value: The value to convert
        :raises ValidationError: if a valid return value cannot be determined.
        :return: An enumeration value or the canonical empty value if value is
            one of our empty_values, or the value itself if this is a
            non-strict field and the value is of a matching primitive type
        """

        if value in self.empty_values:
            return self.empty_value
        if self.enum is not None and not isinstance(value, self.enum):
            try:
                value = self.enum(value)
            except (TypeError, ValueError):
                try:
                    value = self._coerce_to_value_type(value)
                    value = self.enum(value)
                except (TypeError, ValueError) as err:
                    if self.strict or not isinstance(
                            value,
                            type(self.enum.values[0])
                    ):
                        raise ValidationError(
                            f'{value} is not a valid {self.enum}.',
                            code='invalid_choice',
                            params={'value': value},
                        ) from err
        return value

    def prepare_value(self, value: Any) -> Any:
        """Must return the raw enumeration value type"""
        value = self._coerce(value)
        return super().prepare_value(
            value.value
            if isinstance(value, self.enum)
            else value
        )

    def to_python(self, value: Any) -> Union[Choices, Any]:
        """Return the value as its full enumeration object"""
        return self._coerce(value)

    def valid_value(self, value: Any) -> bool:
        """Return false if this value is not valid"""
        try:
            self._coerce(value)
            return True
        except ValidationError:
            return False
