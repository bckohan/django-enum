"""Enumeration support for django model forms"""

from copy import copy
from decimal import DecimalException
from enum import Enum
from typing import Any, Iterable, List, Optional, Protocol, Sequence, Tuple, Type, Union

from django.core.exceptions import ValidationError
from django.db.models import Choices
from django.forms.fields import (
    Field,
    TypedChoiceField,
    TypedMultipleChoiceField,
)
from django.forms.widgets import Select, SelectMultiple

from django_enum.utils import choices as get_choices
from django_enum.utils import determine_primitive, with_typehint

__all__ = [
    "NonStrictSelect",
    "NonStrictSelectMultiple",
    "FlagSelectMultiple",
    "EnumChoiceField",
    "EnumFlagField",
]


_SelectChoices = Iterable[Union[Tuple[Any, Any], Tuple[str, Iterable[Tuple[Any, Any]]]]]

_Choice = Tuple[Any, Any]
_ChoiceNamedGroup = Tuple[str, Iterable[_Choice]]
_FieldChoices = Iterable[Union[_Choice, _ChoiceNamedGroup]]


class _ChoicesCallable(Protocol):
    def __call__(self) -> _FieldChoices: ...


_ChoicesParameter = Union[_FieldChoices, _ChoicesCallable]


class _CoerceCallable(Protocol):
    def __call__(self, value: Any, /) -> Any: ...


class _Unspecified:
    """
    Marker used by EnumChoiceField to determine if empty_value
    was overridden
    """


class NonStrictMixin(with_typehint(Select)):  # type: ignore
    """
    Mixin to add non-strict behavior to a widget, this makes sure the set value
    appears as a choice if it is not one of the enumeration choices.
    """

    choices: _SelectChoices

    def render(self, *args, **kwargs):
        """
        Before rendering if we're a non-strict field and our value is not
        one of our choices, we add it as an option.
        """

        value: Any = getattr(kwargs.get("value"), "value", kwargs.get("value"))
        if value not in EnumChoiceField.empty_values and value not in (
            choice[0] for choice in self.choices
        ):
            self.choices = list(self.choices) + [(value, str(value))]
        return super().render(*args, **kwargs)


class NonStrictSelect(NonStrictMixin, Select):
    """
    A Select widget for non-strict EnumChoiceFields that includes any existing
    non-conforming value as a choice option.
    """


class FlagSelectMultiple(SelectMultiple):
    """
    A SelectMultiple widget for EnumFlagFields.
    """


class NonStrictSelectMultiple(NonStrictMixin, SelectMultiple):
    """
    A SelectMultiple widget for non-strict EnumFlagFields that includes any
    existing non-conforming value as a choice option.
    """


class ChoiceFieldMixin(
    with_typehint(TypedChoiceField)  # type: ignore
):
    """
    Mixin to adapt base model form ChoiceFields to use on EnumFields.

    :param enum: The Enumeration type
    :param empty_value: Allow users to define what empty is because some
        enumeration types might use an empty value (i.e. empty string) as an
        enumeration value. This value will be returned when any "empty" value
        is encountered. If unspecified the default empty value of '' is
        returned.
    :param empty_values: Override the list of what are considered to be empty
        values. Defaults to TypedChoiceField.empty_values.
    :param strict: If False, values not included in the enumeration list, but
        of the same primitive type are acceptable.
    :param choices: Override choices, otherwise enumeration choices attribute
        will be used.
    :param kwargs: Any additional parameters to pass to ChoiceField base class.
    """

    _enum_: Optional[Type[Enum]] = None
    _primitive_: Optional[Type] = None
    _strict_: bool = True
    empty_value: Any = ""
    empty_values: Sequence[Any] = list(TypedChoiceField.empty_values)

    _empty_value_overridden_: bool = False
    _empty_values_overridden_: bool = False

    choices: _ChoicesParameter

    def __init__(
        self,
        enum: Optional[Type[Enum]] = _enum_,
        primitive: Optional[Type] = _primitive_,
        *,
        empty_value: Any = _Unspecified,
        strict: bool = _strict_,
        empty_values: Union[List[Any], Type[_Unspecified]] = _Unspecified,
        choices: _ChoicesParameter = (),
        coerce: Optional[_CoerceCallable] = None,
        **kwargs,
    ):
        self._strict_ = strict
        self._primitive_ = primitive
        if not self.strict:
            kwargs.setdefault("widget", NonStrictSelect)

        if empty_values is _Unspecified:
            self.empty_values = copy(list(TypedChoiceField.empty_values))
        else:
            assert isinstance(empty_values, list)
            self.empty_values = empty_values
            self._empty_values_overridden_ = True

        super().__init__(
            choices=choices or getattr(self.enum, "choices", choices),
            coerce=coerce or self.default_coerce,
            **kwargs,
        )

        if empty_value is not _Unspecified:
            self._empty_value_overridden_ = True
            if (
                empty_value not in self.empty_values
                and not self._empty_values_overridden_
            ):
                self.empty_values = [empty_value, *self.empty_values]
            self.empty_value = empty_value

        if enum:
            self.enum = enum

    @property
    def strict(self):
        """strict fields allow non-enumeration values"""
        return self._strict_

    @strict.setter
    def strict(self, strict):
        self._strict_ = strict

    @property
    def primitive(self):
        """
        The most appropriate primitive non-Enumeration type that can represent
        all enumeration values.
        """
        return self._primitive_

    @primitive.setter
    def primitive(self, primitive):
        self._primitive_ = primitive

    @property
    def enum(self):
        """the class of the enumeration"""
        return self._enum_

    @enum.setter
    def enum(self, enum):
        self._enum_ = enum
        self._primitive_ = self._primitive_ or determine_primitive(enum)
        self.choices = self.choices or get_choices(self.enum)
        # remove any of our valid enumeration values or symmetric properties
        # from our empty value list if there exists an equivalency
        if not self._empty_values_overridden_:
            members = self.enum.__members__.values()
            self.empty_values = [val for val in self.empty_values if val not in members]
        if (
            not self._empty_value_overridden_
            and self.empty_value not in self.empty_values
            and self.empty_values
        ):
            self.empty_value = self.empty_values[0]

        if self.empty_value not in self.empty_values:
            raise ValueError(
                f"Enumeration value {repr(self.empty_value)} is"
                f"equivalent to {self.empty_value}, you must "
                f"specify a non-conflicting empty_value."
            )

    def _coerce_to_value_type(self, value: Any) -> Any:
        """Coerce the value to the enumerations value type"""
        return self.primitive(value)

    def prepare_value(self, value: Any) -> Any:
        """Must return the raw enumeration value type"""
        value = self._coerce(value)
        return super().prepare_value(
            value.value if isinstance(value, self.enum) else value
        )

    def to_python(self, value: Any) -> Any:
        """Return the value as its full enumeration object"""
        return self._coerce(value)

    def valid_value(self, value: Any) -> bool:
        """Return false if this value is not valid"""
        try:
            self._coerce(value)
            return True
        except ValidationError:
            return False

    def default_coerce(self, value: Any) -> Any:
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
        if self.enum is not None and not isinstance(value, self.enum):
            try:
                value = self.enum(value)
            except (TypeError, ValueError):
                try:
                    value = self._coerce_to_value_type(value)
                    value = self.enum(value)
                except (TypeError, ValueError, DecimalException):
                    try:
                        value = self.enum[value]
                    except KeyError as err:
                        assert self.primitive
                        if self.strict or not isinstance(value, self.primitive):
                            raise ValidationError(
                                f"{value} is not a valid {self.enum}.",
                                code="invalid_choice",
                                params={"value": value},
                            ) from err
        return value

    def validate(self, value):
        """Validate that the input is in self.choices."""
        # there is a bug in choice field where it passes 0 values, we skip over
        # its implementation and call the parent class's validate
        Field.validate(self, value)
        if value not in self.empty_values and not self.valid_value(value):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )


class EnumChoiceField(ChoiceFieldMixin, TypedChoiceField):  # type: ignore
    """
    The default ``ChoiceField`` will only accept the base enumeration values.
    Use this field on forms to accept any value mappable to an enumeration
    including any labels or symmetric properties.
    """


class EnumFlagField(ChoiceFieldMixin, TypedMultipleChoiceField):  # type: ignore
    """
    The default ``TypedMultipleChoiceField`` will only accept the base
    enumeration values. Use this field on forms to accept any value mappable
    to an enumeration including any labels or symmetric properties.

    Behavior:

    if no select value in post data:
        if null=True, no choice is null.
        If null=False, no choice is Enum(0)
    if select value in post data:
        if null=True or False, no choice is Enum(0)

    if strict=False, values can be outside of the enumerations
    """

    def __init__(
        self,
        enum: Optional[Type[Choices]] = None,
        *,
        empty_value: Any = _Unspecified,
        strict: bool = ChoiceFieldMixin._strict_,
        empty_values: Union[List[Any], Type[_Unspecified]] = _Unspecified,
        choices: _ChoicesParameter = (),
        **kwargs,
    ):
        super().__init__(
            enum=enum,
            empty_value=(
                enum(0) if enum and empty_value is _Unspecified else empty_value
            ),
            strict=strict,
            empty_values=empty_values,
            choices=choices,
            **kwargs,
        )
