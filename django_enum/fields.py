"""
Support for Django model fields built from enumeration types.
"""
from enum import Enum, Flag
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from django.core.exceptions import ValidationError
from django.db.models import (
    BigIntegerField,
    BinaryField,
    CharField,
    Field,
    FloatField,
    IntegerField,
    Model,
    PositiveBigIntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    SmallIntegerField,
)
from django.db.models.query_utils import DeferredAttribute
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_enum.choices import choices, values
from django_enum.forms import (
    EnumChoiceField,
    EnumFlagField,
    FlagSelectMultiple,
    NonStrictSelect,
    NonStrictSelectMultiple,
)

T = TypeVar('T')  # pylint: disable=C0103


def with_typehint(baseclass: Type[T]) -> Type[T]:
    """
    Change inheritance to add Field type hints when type checking is running.
    This is just more simple than defining a Protocol - revisit if Django
    provides Field protocol - should also just be a way to create a Protocol
    from a class?

    This is icky but it works - revisit in future.
    """
    if TYPE_CHECKING:
        return baseclass  # pragma: no cover
    return object  # type: ignore


class ToPythonDeferredAttribute(DeferredAttribute):
    """
    Extend DeferredAttribute descriptor to run a field's to_python method on a
    value anytime it is set on the model. This is used to ensure a EnumFields
    on models are always of their Enum type.
    """

    def __set__(self, instance: Model, value: Any):
        try:
            instance.__dict__[self.field.name] = self.field.to_python(value)
        except (ValidationError, ValueError):
            # Django core fields allow assignment of any value, we do the same
            instance.__dict__[self.field.name] = value


class EnumMixin(
    # why can't mypy handle the line below?
    with_typehint(Field)  # type: ignore
):
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

    _enum_: Optional[Type[Enum]] = None
    _strict_: bool = True
    _coerce_: bool = True
    _primitive_: Any

    descriptor_class = ToPythonDeferredAttribute

    # use properties to disable setters
    @property
    def enum(self) -> Type[Enum]:
        """The enumeration type"""
        return self._enum_

    @property
    def strict(self) -> bool:
        """True if the field requires values to be valid enumeration values"""
        return self._strict_

    @property
    def coerce(self) -> bool:
        """
        False if the field should not coerce values to the enumeration
        type
        """
        return self._coerce_

    @property
    def primitive(self) -> Optional[Type]:
        """
        The most appropriate primitive non-Enumeration type that can represent
        all enumeration values.
        """
        return self._primitive_

    def _coerce_to_value_type(self, value: Any) -> Optional[Enum]:
        """Coerce the value to the enumerations value type"""
        # note if enum type is int and a floating point is passed we could get
        # situations like X.xxx == X - this is acceptable
        if value is not None and self.enum:
            return self.primitive(value)
        return value

    def __init__(
            self,
            *args,
            enum: Optional[Type[Enum]] = None,
            primitive: Optional[Type] = None,
            strict: bool = _strict_,
            coerce: bool = _coerce_,
            **kwargs
    ):
        self._enum_ = enum
        self._primitive_ = primitive
        self._strict_ = strict if enum else False
        self._coerce_ = coerce if enum else False
        if self.enum is not None:
            kwargs.setdefault('choices', choices(enum))

        super().__init__(*args, **kwargs)

    def _try_coerce(
            self,
            value: Any,
            force: bool = False
    ) -> Union[Enum, Any]:
        """
        Attempt coercion of value to enumeration type instance, if unsuccessful
        and non-strict, coercion to enum's primitive type will be done,
        otherwise a ValueError is raised.
        """
        if (
            (self.coerce or force)
            and self.enum is not None
            and not isinstance(value, self.enum)
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
                            self.primitive
                        ):
                            raise ValueError(
                                f"'{value}' is not a valid "
                                f"{self.enum.__name__} required by field "
                                f"{self.name}."
                            ) from err
        elif not self.coerce:
            try:
                return self._coerce_to_value_type(value)
            except (TypeError, ValueError) as err:
                raise ValueError(
                    f"'{value}' is not a valid {self.primitive} "
                    f"required by field {self.name}."
                ) from err
        return value

    def deconstruct(self) -> Tuple[str, str, List, dict]:
        """
        Preserve field migrations. Strict and coerce are omitted because
        reconstructed fields are *always* non-strict and coerce is always
        False.

        .. warning::

            Do not add enum to kwargs! It is important that migration files not
            reference enum classes that might be removed from the code base in
            the future as this would break older migration files! We simply use
            the choices tuple, which is plain old data and entirely sufficient
            to de/reconstruct our field.

        See deconstruct_
        """
        name, path, args, kwargs = super().deconstruct()
        if self.enum is not None:
            kwargs['choices'] = choices(self.enum)

        if 'default' in kwargs:
            # ensure default in deconstructed fields is always the primitive
            # value type
            kwargs['default'] = getattr(
                self.get_default(),
                'value',
                self.get_default()
            )

        return name, path, args, kwargs

    def get_prep_value(self, value: Any) -> Any:
        """
        Convert the database field value into the Enum type.

        See get_prep_value_
        """
        if self.enum:
            try:
                value = self._try_coerce(value, force=True)
                if isinstance(value, self.enum):
                    value = value.value
            except (ValueError, TypeError):
                if value is not None:
                    raise
        return super().get_prep_value(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        """
        Convert the field value into the Enum type and then pull its value
        out.

        See get_db_prep_value_
        """
        if self.enum:
            try:
                value = self._try_coerce(value, force=True)
                if isinstance(value, self.enum):
                    value = value.value
            except (ValueError, TypeError):
                if value is not None:
                    raise
        return super().get_db_prep_value(value, connection, prepared)

    def from_db_value(
            self,
            value: Any,
            expression,  # pylint: disable=W0613
            connection  # pylint: disable=W0613
    ) -> Any:
        """
        Convert the database field value into the Enum type.

        See from_db_value_
        """
        value = getattr(super, 'from_db_value', lambda v: v)(value)
        try:
            return self._try_coerce(value)
        except (ValueError, TypeError):
            if value is None:
                return value
            raise

    def to_python(self, value: Any) -> Union[Enum, Any]:
        """
        Converts the value in the enumeration type.

        See to_python_

        :param value: The value to convert
        :return: The converted value
        :raises ValidationError: If the value is not mappable to a valid
            enumeration
        """
        try:
            return self._try_coerce(value)
        except (ValueError, TypeError) as err:
            if value is None:
                return value
            raise ValidationError(
                f"'{value}' is not a valid "
                f"{self.enum.__name__ if self.enum else ''}."
            ) from err

    def get_default(self) -> Any:
        """Wrap get_default in an enum type coercion attempt"""
        if self.has_default():
            try:
                return self.to_python(super().get_default())
            except ValidationError:
                return super().get_default()
        elif self.enum and issubclass(self.enum, Flag):
            return 0
        return super().get_default()

    def validate(self, value: Any, model_instance: Model):
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
            self._try_coerce(value, force=True)
        except ValueError as err:
            raise ValidationError(
                str(err),
                code='invalid_choice',
                params={'value': value}
            ) from err

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):

        # super().formfield deletes anything unrecognized from kwargs that
        #   we try to pass in. Very annoying because we have to
        #   un-encapsulate some of this initialization logic, this makes our
        #   EnumChoiceField pretty ugly!

        is_multi = self.enum and issubclass(self.enum, Flag)
        if is_multi and self.enum:
            kwargs['empty_value'] = self.enum(0)
            # why fail? - does this fail for single select too?
            #kwargs['show_hidden_initial'] = True

        if not self.strict:
            kwargs.setdefault(
                'widget',
                NonStrictSelectMultiple if is_multi else NonStrictSelect
            )
        elif is_multi:
            kwargs.setdefault('widget', FlagSelectMultiple)

        form_field = super().formfield(
            form_class=form_class,
            choices_form_class=(
                choices_form_class or
                EnumFlagField if is_multi else EnumChoiceField
            ),
            **kwargs
        )

        # we can't pass these in kwargs because formfield() strips them out
        form_field.enum = self.enum
        form_field.strict = self.strict
        form_field.primitive = self.primitive
        return form_field

    def get_choices(self, **kwargs):  # pylint: disable=W0221
        if self.enum and issubclass(self.enum, Flag):
            kwargs['blank_choice'] = [(self.enum(0), '---------')]
        return super().get_choices(**kwargs)


class EnumCharField(EnumMixin, CharField):
    """
    A database field supporting enumerations with character values.
    """

    def __init__(self, *args, enum=None, **kwargs):
        kwargs.setdefault(
            'max_length',
            max((
                len(choice[0])
                for choice in kwargs.get('choices', choices(enum))
            ))
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


class EnumBitField(EnumMixin, BinaryField):
    """
    A database field supporting enumerations with integer values that require
    more than 64 bits. This field only works for Enums that inherit from int.
    This field stores enum values in big endian byte order.
    """

    description = _('A bit field wider than the standard word size.')

    def __init__(self, *args, editable=True, **kwargs):
        super().__init__(*args, editable=editable, **kwargs)

    @cached_property
    def signed(self):
        """True if the enum has negative values"""
        for val in self.enum or []:
            if val.value < 0:
                return True
        return False

    def get_prep_value(self, value: Any) -> Any:
        """
        Convert the database field value into the Enum type then convert that
        enum value into the smallest number of bytes that can hold it.

        See get_prep_value_
        """
        if value is None or isinstance(value, (bytes, memoryview, bytearray)):
            return value

        value = self._try_coerce(value, force=True)
        value = getattr(value, 'value', value)
        value = value.to_bytes(
            (value.bit_length() + 7) // 8,
            byteorder='big',
            signed=self.signed
        )
        return BinaryField.get_prep_value(self, value)

    def get_db_prep_value(self, value, connection, prepared=False):
        """
        Convert the field value into the Enum type and then pull its value
        out.

        See get_db_prep_value_
        """
        if value is None or isinstance(value, (bytes, memoryview, bytearray)):
            return value

        value = self._try_coerce(value, force=True)
        value = getattr(value, 'value', value)
        value = value.to_bytes(
            (value.bit_length() + 7) // 8,
            byteorder='big',
            signed=self.signed
        )
        return BinaryField.get_db_prep_value(
            self,
            value,
            connection,
            prepared
        )

    def from_db_value(
            self,
            value: Any,
            expression,  # pylint: disable=W0613
            connection  # pylint: disable=W0613
    ) -> Any:
        """
        Convert the database field value into the Enum type.

        See from_db_value_
        """
        if value is None:  # pragma: no cover
            return value
        return super().from_db_value(
            int.from_bytes(value, byteorder='big', signed=self.signed),
            expression,
            connection
        )


class _EnumFieldMetaClass(type):

    SUPPORTED_PRIMITIVES = {int, str, float}

    def __new__(  # pylint: disable=R0911
            mcs,
            enum: Type[Enum],
            primitive: Type
    ) -> Type[EnumMixin]:
        """
        Construct a new Django Field class given the Enumeration class. The
        correct Django field class to inherit from is determined based on the
        primitive type seen in the Enumeration class's inheritance tree.

        :param enum: The class of the Enumeration to build a field class for
        :param primitive: The primitive type to use to determine the Django
            field class to inherit from
        """
        if issubclass(primitive, float):
            return EnumFloatField

        if issubclass(primitive, int):
            min_value = min((val for val in values(enum) if val is not None))
            max_value = max((val for val in values(enum) if val is not None))
            if min_value < 0:
                if (
                    min_value < -9223372036854775808 or
                    max_value > 9223372036854775807
                ):
                    return EnumBitField
                if min_value < -2147483648 or max_value > 2147483647:
                    return EnumBigIntegerField
                if min_value < -32768 or max_value > 32767:
                    return EnumIntegerField
                return EnumSmallIntegerField

            if max_value > 9223372036854775807:
                return EnumBitField
            if max_value > 2147483647:
                return EnumPositiveBigIntegerField
            if max_value > 32767:
                return EnumPositiveIntegerField
            return EnumPositiveSmallIntegerField

        if issubclass(primitive, str):
            return EnumCharField

        # if issubclass(primitive, datetime):
        #     return EnumDateTimeField
        #
        # if issubclass(primitive, date):
        #     return EnumDateField
        #
        # if issubclass(primitive, timedelta):
        #     return EnumDurationField

        raise NotImplementedError(
            f'EnumField does not support enumerations of primitive type '
            f'{primitive}'
        )


def determine_primitive(enum: Type[Enum]) -> Optional[Type]:
    """
    Determine the python type most appropriate to represent all values of the
    enumeration class. The primitive type determination algorithm is thus:

        * Determine the types of all the values in the enumeration
        * Determine the first supported primitive type in the enumeration class
          inheritance tree
        * If there is only one value type, use its type as the primitive
        * If there are multiple value types and they are all subclasses of
          the class primitive type, use the class primitive type. If there is
          no class primitive type use the first supported primitive type that
          all values are symmetrically coercible to. If there is no such type,
          return None

    By definition all values of the enumeration with the exception of None
    may be coerced to the primitive type and vice-versa.

    :param enum: The enumeration class to determine the primitive type for
    :return: A python type or None if no primitive type could be determined
    """
    primitive = None
    if enum:
        for prim in enum.__mro__:
            if primitive:
                break
            for supported in _EnumFieldMetaClass.SUPPORTED_PRIMITIVES:
                if issubclass(prim, supported):
                    primitive = supported
                    break
        value_types = set()
        for value in values(enum):
            if value is not None:
                value_types.add(type(value))

        value_types = list(value_types)
        if len(value_types) > 1 and primitive is None:
            for candidate in _EnumFieldMetaClass.SUPPORTED_PRIMITIVES:
                works = True
                for value in values(enum):
                    if value is None:
                        continue
                    try:
                        # test symmetric coercibility
                        works &= type(value)(candidate(value)) == value
                    except (TypeError, ValueError):
                        works = False
                if works:
                    return candidate
        elif value_types:
            return value_types[0]
    return primitive


def EnumField(  # pylint: disable=C0103
        enum: Type[Enum],
        *field_args,
        primitive: Optional[Type] = None,
        **field_kwargs
) -> EnumMixin:
    """
    *This is a function, not a type*. Some syntactic sugar that wraps the enum
    field metaclass so that we can cleanly create enums like so:

    .. code-block::

        class MyModel(models.Model):

            class EnumType(IntegerChoices):

                VAL1 = 1, _('Value 1')
                VAL2 = 2, _('Value 2')
                VAL3 = 3, _('Value 3')

            field_name = EnumField(EnumType)

    :param enum: The class of the enumeration.
    :param field_args: Any standard unnamed field arguments for the base
        field type.
    :param primitive: Override the primitive type of the enumeration. By
        default this primitive type is determined by the types of the
        enumeration values and the Enumeration class inheritance tree. It
        is almost always unnecessary to override this value. The primitive type
        is used to determine which Django field type the EnumField will
        inherit from and will be used to coerce the enumeration values to a
        python type other than the enumeration class. All enumeration values
        with the exception of None must be symmetrically coercible to the
        primitive type.
    :param field_kwargs: Any standard named field arguments for the base
        field type.
    :return: An object of the appropriate enum field type
    """
    # determine the primitive type of the enumeration class and perform some
    # sanity checks
    primitive = primitive or determine_primitive(enum)
    if primitive is None:
        raise ValueError(
            f'EnumField is unable to determine the primitive type for {enum}. '
            f'consider providing one explicitly using the primitive argument.'
        )

    # make sure all enumeration values are symmetrically coercible to
    # the primitive, if they are not this could cause some strange behavior
    for value in values(enum):
        if value is None:
            continue
        try:
            assert type(value)(primitive(value)) == value
        except (TypeError, ValueError, AssertionError) as coerce_error:
            raise ValueError(
                f'Not all {enum} values are symmetrically coercible to '
                f'primitive type {primitive}'
            ) from coerce_error

    return _EnumFieldMetaClass(enum, primitive)(
        enum=enum,
        primitive=primitive,
        *field_args,
        **field_kwargs
    )
