"""Support for django rest framework symmetric serialization"""

__all__ = ["EnumField", "EnumFieldMixin"]

import inspect
from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException
from enum import Enum
from typing import Any, Dict, Optional, Type, Union

from rest_framework.fields import (
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    DecimalField,
    DurationField,
    Field,
    FloatField,
    IntegerField,
    TimeField,
)
from rest_framework.serializers import ModelSerializer
from rest_framework.utils.field_mapping import get_field_kwargs

from django_enum import EnumField as EnumModelField
from django_enum.utils import (
    choices,
    decimal_params,
    determine_primitive,
    with_typehint,
)


class ClassLookupDict:
    """
    A dict-like object that looks up values using the MRO of a class or
    instance. Similar to DRF's ClassLookupDict but returns None instead
    of raising KeyError and allows classes or object instances to be
    used as lookup keys.

    :param mapping: A dictionary containing a mapping of class types to
        values.
    """

    def __init__(self, mapping: Dict[Type[Any], Any]):
        self.mapping = mapping

    def __getitem__(self, key: Any) -> Optional[Any]:
        """
        Fetch the given object for the type or type of the given object.

        :param key: An object instance or class type
        :return: The mapped value to the object instance's class or the
            passed class type. Inheritance is honored. None is returned
            if no mapping is present.
        """
        for cls in inspect.getmro(
            getattr(
                key,
                "_proxy_class",
                key if isinstance(key, type) else getattr(key, "__class__"),
            )
        ):
            if cls in self.mapping:
                return self.mapping.get(cls, None)
        return None


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
    primitive: Type[Any]
    strict: bool = True
    primitive_field: Optional[Type[Field]] = None

    def __init__(self, enum: Type[Enum], strict: bool = strict, **kwargs):
        self.enum = enum
        self.primitive = determine_primitive(enum)  # type: ignore
        assert (
            self.primitive is not None
        ), f"Unable to determine primitive type for {enum}"
        self.strict = strict
        self.choices = kwargs.pop("choices", choices(enum))
        field_name = kwargs.pop("field_name", None)
        model_field = kwargs.pop("model_field", None)
        if not self.strict:
            # if this field is not strict, we instantiate its primitive
            # field type so we can fall back to its to_internal_value
            # method if the value is not a valid enum value
            primitive_field_cls = ClassLookupDict(
                {
                    str: CharField,
                    int: IntegerField,
                    float: FloatField,
                    date: DateField,
                    datetime: DateTimeField,
                    time: TimeField,
                    timedelta: DurationField,
                    Decimal: DecimalField,
                }
            )[self.primitive]
            if primitive_field_cls:
                field_kwargs = {
                    **kwargs,
                    **{
                        key: val
                        for key, val in (
                            get_field_kwargs(field_name, model_field)
                            if field_name and model_field
                            else {}
                        ).items()
                        if key not in ["model_field", "field_name", "choices"]
                    },
                }
                if primitive_field_cls is not CharField:
                    field_kwargs.pop("allow_blank", None)
                if primitive_field_cls is DecimalField:
                    field_kwargs = {
                        **field_kwargs,
                        **decimal_params(
                            self.enum,
                            max_digits=field_kwargs.pop("max_digits", None),
                            decimal_places=field_kwargs.pop("decimal_places", None),
                        ),
                    }
                self.primitive_field = primitive_field_cls(**field_kwargs)
        super().__init__(choices=self.choices, **kwargs)

    def to_internal_value(self, data: Any) -> Union[Enum, Any]:
        """
        Transform the *incoming* primitive data into an enum instance.
        """
        if data == "" and self.allow_blank:
            return ""

        if not isinstance(data, self.enum):
            try:
                data = self.enum(data)
            except (TypeError, ValueError):
                try:
                    data = self.primitive(data)
                    data = self.enum(data)
                except (TypeError, ValueError, DecimalException):
                    if self.strict:
                        self.fail("invalid_choice", input=data)
                    elif self.primitive_field:
                        return self.primitive_field.to_internal_value(data)
        return data

    def to_representation(self, value: Any) -> Any:
        """
        Transform the *outgoing* enum value into its primitive value.
        """
        return getattr(value, "value", value)


class EnumFieldMixin(with_typehint(ModelSerializer)):  # type: ignore
    """
    A mixin for ModelSerializers that adds auto-magic support for
    EnumFields.
    """

    def build_standard_field(self, field_name, model_field):
        """
        The default implementation of build_standard_field will set any
        field with choices to a ChoiceField. This will override that for
        EnumFields and add enum and strict arguments to the field's kwargs.

        To use this mixin, include it before ModelSerializer in your
        serializer's class hierarchy:

        ..code-block:: python

            from django_enum.drf import EnumFieldMixin
            from rest_framework.serializers import ModelSerializer

            class MySerializer(EnumFieldMixin, ModelSerializer):

                class Meta:
                    model = MyModel
                    fields = '__all__'


        :param field_name: The name of the field on the serializer
        :param model_field: The Field instance on the model
        :return: A 2-tuple, the first element is the field class, the
            second is the kwargs for the field
        """
        field_class = ClassLookupDict({EnumModelField: EnumField})[model_field]
        if field_class:
            return field_class, {
                "enum": model_field.enum,
                "strict": model_field.strict,
                "field_name": field_name,
                "model_field": model_field,
                **super().build_standard_field(field_name, model_field)[1],
            }
        return super().build_standard_field(field_name, model_field)
