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

    def _coerce(self, value):
        """
        Validate that the value is coercible to the enumeration type.
        """
        if value == self.empty_value or value in self.empty_values:
            return self.empty_value
        try:
            value = self.enum(value).value
        except (ValueError, TypeError, ValidationError) as err:
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
