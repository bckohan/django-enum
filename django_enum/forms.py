"""Enumeration support for django model forms"""
from django.core.exceptions import ValidationError
from django.forms.fields import ChoiceField


class EnumChoiceField(ChoiceField):
    """
    The default ``ChoiceField`` will only accept the base enumeration values.
    Use this field on forms to accept any value mappable to an enumeration
    including any labels or symmetric properties.
    """

    def __init__(self, enum, *, empty_value='', choices=(), **kwargs):
        self.enum = enum
        self.empty_value = empty_value
        super().__init__(
            choices=choices or getattr(self.enum, 'choices', ()),
            **kwargs
        )

    def _coerce_to_value_type(self, value):
        """Coerce the value to the enumerations value type"""
        return type(self.enum.values[0])(value)

    def _coerce(self, value):
        if value == self.empty_value or value in self.empty_values:
            return self.empty_value
        if self.enum is not None and not isinstance(value, self.enum):
            try:
                value = self.enum(value)
            except (TypeError, ValueError):
                try:
                    value = self.enum(self._coerce_to_value_type(value))
                except (TypeError, ValueError) as err:
                    raise ValidationError(
                        f'{value} is not a valid {self.enum}.',
                        code='invalid_choice',
                        params={'value': value},
                    ) from err
        return value

    def clean(self, value):
        return super().clean(self._coerce(value))

    # def prepare_value(self, value):
    #     return value
    #
    # def to_python(self, value):
    #     return value
    #
    # def validate(self, value):
    #     if value in self.empty_values and self.required:
    #         raise ValidationError(
    #           self.error_messages['required'], code='required'
    #         )
