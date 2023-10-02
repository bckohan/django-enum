"""Enumeration support for django model forms"""
from enum import Enum
from typing import Any, Iterable, List, Optional, Tuple, Type, Union

from django.core.exceptions import ValidationError
from django.forms.fields import Field, TypedChoiceField
from django.forms.widgets import Select
from django_enum.choices import choices as get_choices
from django_enum.choices import values

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


class EnumChoiceField(TypedChoiceField):
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
    :param empty_values: Override the list of what are considered to be empty
        values.
    :param strict: If False, values not included in the enumeration list, but
        of the same primitive type are acceptable.
    :param choices: Override choices, otherwise enumeration choices attribute
        will be used.
    :param kwargs: Any additional parameters to pass to ChoiceField base class.
    """

    enum_: Optional[Type[Enum]] = None
    strict_: bool = True
    empty_value: Any = ''
    empty_values: List[Any] = TypedChoiceField.empty_values
    choices: Iterable[Tuple[Any, Any]]

    @property
    def strict(self):
        """strict fields allow non-enumeration values"""
        return self.strict_

    @strict.setter
    def strict(self, strict):
        self.strict_ = strict

    @property
    def enum(self):
        """the class of the enumeration"""
        return self.enum_

    @enum.setter
    def enum(self, enum):
        self.enum_ = enum
        self.choices = self.choices or get_choices(self.enum)
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
                    if enum_val == self.empty_value:
                        if self.empty_values:
                            self.empty_value = self.empty_values[0]
                        else:
                            raise ValueError(
                                f'Enumeration value {repr(enum_val)} is'
                                f'equivalent to {self.empty_value}, you must '
                                f'specify a non-conflicting empty_value.'
                            )

    def __init__(
            self,
            enum: Optional[Type[Enum]] = None,
            *,
            empty_value: Any = _Unspecified,
            strict: bool = strict_,
            empty_values: List[Any] = empty_values.copy(),
            choices: Iterable[Tuple[Any, str]] = (),
            **kwargs
    ):
        self.strict = strict
        if not self.strict:
            kwargs.setdefault('widget', NonStrictSelect)

        self.empty_values = empty_values

        super().__init__(
            choices=choices or getattr(self.enum, 'choices', choices),
            coerce=kwargs.pop('coerce', self.coerce),
            **kwargs
        )

        if empty_value is not _Unspecified:
            if empty_value not in self.empty_values:
                self.empty_values.insert(0, empty_value)
            self.empty_value = empty_value

        if enum:
            self.enum = enum

    def _coerce_to_value_type(self, value: Any) -> Any:
        """Coerce the value to the enumerations value type"""
        return type(values(self.enum)[0])(value)

    def coerce(  # pylint: disable=E0202
            self, value: Any
    ) -> Union[Enum, Any]:
        """
        Attempt conversion of value to an enumeration value and return it
        if successful.

        .. note::

            When used to represent a model field, by default the model field's
            to_python method will be substituted for this method.

        :param value: The value to convert
        :raises ValidationError: if a valid return value cannot be determined.
        :return: An enumeration value or the canonical empty value if value is
            one of our empty_values, or the value itself if this is a
            non-strict field and the value is of a matching primitive type
        """
        if (
            self.enum is not None and
            not isinstance(value, self.enum)  # pylint: disable=R0801
        ):
            try:
                value = self.enum(value)
            except (TypeError, ValueError):
                try:
                    value = self._coerce_to_value_type(value)
                    value = self.enum(value)
                except (TypeError, ValueError):
                    try:
                        value = self.enum[value]
                    except KeyError as err:
                        if self.strict or not isinstance(
                            value,
                            type(values(self.enum)[0])
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

    def to_python(self, value: Any) -> Union[Enum, Any]:
        """Return the value as its full enumeration object"""
        return self._coerce(value)

    def valid_value(self, value: Any) -> bool:
        """Return false if this value is not valid"""
        try:
            self._coerce(value)
            return True
        except ValidationError:
            return False

    def validate(self, value):
        """Validate that the input is in self.choices."""
        # there is a bug in choice field where it passes 0 values, we skip over
        # its implementation and call the parent class's validate
        Field.validate(self, value)
        if value not in self.empty_values and not self.valid_value(value):
            raise ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
                params={'value': value},
            )
