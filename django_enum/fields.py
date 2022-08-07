"""
Support for Django model fields built from enumeration types.
"""
from django.core.exceptions import ValidationError
from django.db.models import (
    BigIntegerField,
    CharField,
    Choices,
    FloatField,
    IntegerField,
    PositiveBigIntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    SmallIntegerField,
)


class EnumMixin:
    """
    This mixin class turns any Django database field into an enumeration field.
    It works by overriding validation and pre/post database hooks to validate
    and convert any values to the Enumeration type in question.

    :param enum: The enum class
    :param strict: If True (default) the field will throw ValueErrors if the
        value is not coercible to a valid enumeration type.
    :param args: Any standard unnamed field arguments for the underlying
        field type.
    :param field_kwargs: Any standard named field arguments for the underlying
        field type.
    """

    enum = None
    strict = True

    def _coerce_to_value_type(self, value):
        """Coerce the value to the enumerations value type"""
        # note if enum type is int and a floating point is passed we could get
        # situations like X.xxx == X - this is acceptable
        return type(self.enum.values[0])(value)

    def __init__(self, *args, enum=None, strict=strict, **kwargs):
        self.enum = enum
        self.strict = strict if enum else False
        if self.enum is not None:
            kwargs.setdefault('choices', enum.choices if enum else [])
        super().__init__(*args, **kwargs)

    def _try_coerce(self, value):
        if self.enum is not None and not isinstance(value, self.enum):
            try:
                value = self.enum(value)
            except (TypeError, ValueError):
                try:
                    value = self.enum(self._coerce_to_value_type(value))
                except (TypeError, ValueError) as err:
                    if self.strict:
                        raise ValueError(
                            f"'{value}' is not a valid {self.enum.__name__} "
                            f"required by field {self.name}."
                        ) from err
        return value

    def deconstruct(self):
        """
        Preserve enum class for migrations. Strict is omitted because
        reconstructed fields are *always* non-strict sense enum is null.

        See deconstruct_
        """
        name, path, args, kwargs = super().deconstruct()
        if self.enum is not None:
            kwargs['choices'] = self.enum.choices

        return name, path, args, kwargs

    def get_prep_value(self, value):
        """
        Convert the database field value into the Enum type.

        See get_prep_value_
        """
        if value is not None and self.enum is not None:
            value = self._try_coerce(value)
            if isinstance(value, self.enum):
                value = value.value
        return super().get_prep_value(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        """
        Convert the field value into the Enum type and then pull its value
        out.

        See get_db_prep_value_
        """
        if value is not None and self.enum is not None:
            value = self._try_coerce(value)
            if isinstance(value, self.enum):
                value = value.value
        return super().get_db_prep_value(
            value,
            connection,
            prepared
        )

    def from_db_value(
            self,
            value,
            expression,  # pylint: disable=W0613
            connection  # pylint: disable=W0613
    ):
        """
        Convert the database field value into the Enum type.

        See from_db_value_
        """
        if value is None:  # pragma: no cover
            return value
        return self._try_coerce(value)

    def to_python(self, value):
        """
        Converts the value in the enumeration type.

        See to_python_

        :param value: The value to convert
        :return: The converted value
        :raises ValidationError: If the value is not mappable to a valid
            enumeration
        """
        if self.enum is None or isinstance(value, self.enum) or value is None:
            return value

        try:
            return self._try_coerce(value)
        except ValueError as err:
            raise ValidationError(
                f"'{value}' is not a valid {self.enum.__name__}."
            ) from err

    def validate(self, value, model_instance):
        """
        Validates the field as part of model clean routines. Runs super class
        validation routines then tries to convert the value to a valid
        enumeration instance.

        See full_clean_

        :param value: The value to validate
        :param model_instance: The model instance holding the value
        :raises ValidationError: if the value fails validation
        :return:
        """
        try:
            super().validate(value, model_instance)
        except ValidationError as err:
            if err.code != 'invalid_choice':
                raise err
        try:
            self.to_python(value)
        except ValidationError as err:
            raise ValidationError(
                err.message,
                code='invalid_choice',
                params={'value': value}
            ) from err


class EnumCharField(EnumMixin, CharField):
    """
    A database field supporting enumerations with character values.
    """

    def __init__(self, *args, enum=None, **kwargs):
        choices = kwargs.get('choices', enum.choices if enum else [])
        kwargs.setdefault(
            'max_length',
            max([len(choice[0]) for choice in choices])
        )
        super().__init__(*args, enum=enum, **kwargs)


class EnumFloatField(EnumMixin, FloatField):
    """A database field supporting enumerations with floating point values"""


class EnumSmallIntegerField(EnumMixin, SmallIntegerField):
    """
    A database field supporting enumerations with integer values that fit into
    2 bytes or fewer
    """


class EnumPositiveSmallIntegerField(EnumMixin, PositiveSmallIntegerField):
    """
    A database field supporting enumerations with positive (but signed) integer
    values that fit into 2 bytes or fewer
    """


class EnumIntegerField(EnumMixin, IntegerField):
    """
    A database field supporting enumerations with integer values that fit into
    32 bytes or fewer
    """


class EnumPositiveIntegerField(EnumMixin, PositiveIntegerField):
    """
    A database field supporting enumerations with positive (but signed) integer
    values that fit into 32 bytes or fewer
    """


class EnumBigIntegerField(EnumMixin, BigIntegerField):
    """
    A database field supporting enumerations with integer values that fit into
    64 bytes or fewer
    """


class EnumPositiveBigIntegerField(EnumMixin, PositiveBigIntegerField):
    """
    A database field supporting enumerations with positive (but signed) integer
    values that fit into 64 bytes or fewer
    """


class _EnumFieldMetaClass(type):

    SUPPORTED_PRIMITIVES = {int, str, float}

    def __new__(mcs, enum):  # pylint: disable=R0911
        """
        Construct a new Django Field class given the Enumeration class. The
        correct Django field class to inherit from is determined based on the
        primitive type seen in the Enumeration class's inheritance tree.

        :param enum: The class of the Enumeration to build a field class for
        """
        assert issubclass(enum, Choices), \
            f'{enum} must inherit from {Choices}!'
        primitive = mcs.SUPPORTED_PRIMITIVES.intersection(set(enum.__mro__))
        assert len(primitive) == 1, f'{enum} must inherit from exactly one ' \
                                    f'supported primitive type ' \
                                    f'{mcs.SUPPORTED_PRIMITIVES}'

        primitive = list(primitive)[0]

        if primitive is float:
            return EnumFloatField

        if primitive is int:
            values = [define.value for define in enum]
            min_value = min(values)
            max_value = max(values)
            if min_value < 0:
                if min_value < -2147483648 or max_value > 2147483647:
                    return EnumBigIntegerField
                if min_value < -32768 or max_value > 32767:
                    return EnumIntegerField
                return EnumSmallIntegerField

            if max_value > 2147483647:
                return EnumPositiveBigIntegerField
            if max_value > 32767:
                return EnumPositiveIntegerField
            return EnumPositiveSmallIntegerField

        return EnumCharField


def EnumField(enum, *field_args, **field_kwargs):  # pylint: disable=C0103
    """
    Some syntactic sugar that wraps the enum field metaclass so that we can
    cleanly create enums like so:

    .. code-block::

    class MyModel(models.Model):

        class EnumType(IntegerChoices):

            VAL1 = 1, _('Value 1')
            VAL2 = 2, _('Value 2')
            VAL3 = 3, _('Value 3')

        field_name = EnumField(EnumType)

    :param enum: The class of the enumeration.
    :param field_args: Any standard unnamed field arguments for the underlying
        field type.
    :param field_kwargs: Any standard named field arguments for the underlying
        field type.
    :return: An object of the appropriate enum field type
    """
    return _EnumFieldMetaClass(enum)(enum=enum, *field_args, **field_kwargs)
