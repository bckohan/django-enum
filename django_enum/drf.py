"""Support for django rest framework symmetric serialization"""

__all__ = ['EnumField']

try:
    from enum import Enum
    from typing import Any, Type, Union

    from django_enum.choices import choices, values
    from rest_framework.fields import ChoiceField

    class EnumField(ChoiceField):
        """
        A djangorestframework serializer field for Enumeration types. If
        unspecified ModelSerializers will assign django_enum.fields.EnumField
        model field types to ChoiceFields. ChoiceFields do not accept
        symmetrical values, this field will.

        :param enum: The type of the Enumeration of the field
        :param strict: If True (default) only values in the Enumeration type
            will be acceptable. If False, no errors will be thrown if other
            values of the same primitive type are used
        :param kwargs: Any other named arguments applicable to a ChoiceField
            will be passed up to the base classes.
        """

        enum: Type[Enum]
        strict: bool = True

        def __init__(
                self,
                enum: Type[Enum],
                strict: bool = strict,
                **kwargs
        ):
            self.enum = enum
            self.strict = strict
            self.choices = kwargs.pop('choices', choices(enum))
            super().__init__(choices=self.choices, **kwargs)

        def to_internal_value(self, data: Any) -> Union[Enum, Any]:
            """
            Transform the *incoming* primitive data into an enum instance.
            """
            if data == '' and self.allow_blank:
                return ''

            if not isinstance(data, self.enum):
                try:
                    data = self.enum(data)
                except (TypeError, ValueError):
                    try:
                        data = type(values(self.enum)[0])(data)
                        data = self.enum(data)
                    except (TypeError, ValueError):
                        if self.strict or not isinstance(
                            data,
                            type(values(self.enum)[0])
                        ):
                            self.fail('invalid_choice', input=data)
            return data

        def to_representation(self, value: Any) -> Any:
            """
            Transform the *outgoing* enum value into its primitive value.
            """
            return getattr(value, 'value', value)


except (ImportError, ModuleNotFoundError):

    class _MissingDjangoRestFramework:
        """Throw error if drf support is used without djangorestframework"""

        def __init__(self, *args, **kwargs):
            raise ImportError(
                f'{self.__class__.__name__} requires djangorestframework to '
                f'be installed.'
            )

    EnumField = _MissingDjangoRestFramework  # type: ignore
