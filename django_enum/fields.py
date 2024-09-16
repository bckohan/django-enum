"""
Support for Django model fields built from enumeration types.
"""

import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException
from enum import Enum, Flag, IntFlag
from functools import reduce
from operator import or_
from typing import Any, Generic, List, Optional, Tuple, Type, TypeVar, Union

from django import VERSION as django_version
from django.core.exceptions import ValidationError
from django.core.validators import DecimalValidator
from django.db.models import (
    NOT_PROVIDED,
    BigIntegerField,
    BinaryField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    DurationField,
    Field,
    FloatField,
    IntegerField,
    Model,
    PositiveBigIntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    Q,
    SmallIntegerField,
    TimeField,
    expressions,
)
from django.db.models.constraints import CheckConstraint
from django.db.models.fields import BLANK_CHOICE_DASH
from django.db.models.query_utils import DeferredAttribute
from django.utils.deconstruct import deconstructible
from django.utils.duration import duration_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from django_enum.forms import (
    EnumChoiceField,
    EnumFlagField,
    FlagSelectMultiple,
    NonStrictSelect,
    NonStrictSelectMultiple,
)
from django_enum.query import (  # HasAllFlagsExtraBigLookup,
    HasAllFlagsLookup,
    HasAnyFlagsLookup,
)
from django_enum.utils import (
    SupportedPrimitive,
    choices,
    decimal_params,
    determine_primitive,
    values,
    with_typehint,
)


class _DatabaseDefault:
    """Spoof DatabaseDefault for Django < 5.0"""


DatabaseDefault = getattr(expressions, "DatabaseDefault", _DatabaseDefault)

CONFORM: Union[Enum, Type[NOT_PROVIDED]]
EJECT: Union[Enum, Type[NOT_PROVIDED]]
STRICT: Union[Enum, Type[NOT_PROVIDED]]

if sys.version_info >= (3, 11):
    from enum import CONFORM, EJECT, STRICT
else:
    CONFORM = EJECT = STRICT = NOT_PROVIDED


MAX_CONSTRAINT_NAME_LENGTH = 64


PrimitiveT = TypeVar("PrimitiveT", bound=Type[SupportedPrimitive])

condition = "check" if django_version[0:2] < (5, 1) else "condition"


@deconstructible
class EnumValidatorAdapter:
    """
    A wrapper for validators that expect a primitive type that enables them
    to receive an Enumeration value instead. Some automatically added field
    validators must be wrapped.
    """

    wrapped: Type

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __call__(self, value):
        return self.wrapped(value.value if isinstance(value, Enum) else value)

    def __eq__(self, other):
        return self.wrapped == other

    def __repr__(self):
        return f"EnumValidatorAdapter({repr(self.wrapped)})"

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return self.wrapped.__getattribute__(name)


class ToPythonDeferredAttribute(DeferredAttribute):
    """
    Extend DeferredAttribute descriptor to run a field's to_python method on a
    value anytime it is set on the model. This is used to ensure a EnumFields
    on models are always of their Enum type.
    """

    def __set__(self, instance: Model, value: Any):
        try:
            instance.__dict__[self.field.name] = (
                value
                if isinstance(value, DatabaseDefault)
                else self.field.to_python(value)
            )
        except (ValidationError, ValueError):
            # Django core fields allow assignment of any value, we do the same
            instance.__dict__[self.field.name] = value


class EnumFieldFactory(type):
    """
    Metaclass for EnumField that allows us to dynamically create a EnumFields
    based on their python Enum class types.
    """

    def __call__(
        cls,
        enum: Optional[Type[Enum]] = None,
        primitive: Optional[Type[SupportedPrimitive]] = None,
        bit_length: Optional[int] = None,
        **field_kwargs,
    ) -> "EnumField":
        """
        Construct a new Django Field class object given the Enumeration class.
        The correct Django field class to inherit from is determined based on
        the primitive type given or determined from the Enumeration class's
        inheritance tree and value types. This dynamic class creation allows us
        to use a single EnumField() initialization call for all enumeration
        types. For example:

        .. code-block::

            class MyModel(models.Model):

                class EnumType(IntegerChoices):

                    VAL1 = 1, _('Value 1')
                    VAL2 = 2, _('Value 2')
                    VAL3 = 3, _('Value 3')

                class EnumTypeChar(TextChoices):

                    VAL1 = 'V1', _('Value 1')
                    VAL2 = 'V2', _('Value 2')

                i_field = EnumField(EnumType)
                c_field = EnumField(EnumTypeChar)

            assert isinstance(MyModel._meta.get_field('i_field'), IntegerField)
            assert isinstance(MyModel._meta.get_field('c_field'), CharField)

            assert isinstance(MyModel._meta.get_field('i_field'), EnumField)
            assert isinstance(MyModel._meta.get_field('c_field'), EnumField)

        :param enum: The class of the enumeration.
        :param primitive: Override the primitive type of the enumeration. By
            default this primitive type is determined by the types of the
            enumeration values and the Enumeration class inheritance tree. It
            is almost always unnecessary to override this value. The primitive
            type is used to determine which Django field type the EnumField
            will inherit from and will be used to coerce the enumeration values
            to a python type other than the enumeration class. All enumeration
            values excluding None must be symmetrically coercible to the
            primitive type.
        :param bit_length: For enumerations of primitive type Integer. Override
            the default bit length of the enumeration. This field determines
            the size of the integer column in the database and by default is
            determined by the minimum and maximum values of the enumeration. It
            may be necessary to override this value for flag enumerations that
            use KEEP boundary behavior to store extra information in higher
            bits.
        :param field_kwargs: Any standard named field arguments for the base
            field type.
        :return: An object of the appropriate enum field type
        """
        # determine the primitive type of the enumeration class and perform
        # some sanity checks
        if cls is not EnumField:
            if bit_length is not None:
                field_kwargs["bit_length"] = bit_length
            return type.__call__(cls, enum=enum, primitive=primitive, **field_kwargs)
        if enum is None:
            raise ValueError(
                "EnumField must be initialized with an `enum` argument that "
                "specifies the python Enum class."
            )
        primitive = primitive or determine_primitive(enum)
        if primitive is None:
            raise ValueError(
                f"EnumField is unable to determine the primitive type for "
                f"{enum}. consider providing one explicitly using the "
                f"primitive argument."
            )

        # make sure all enumeration values are symmetrically coercible to
        # the primitive, if they are not this could cause some strange behavior
        for value in values(enum):
            if value is None or type(value) is primitive:
                continue
            try:
                assert type(value)(primitive(value)) == value  # type: ignore
            except (TypeError, ValueError, AssertionError) as coerce_error:
                raise ValueError(
                    f"Not all {enum} values are symmetrically coercible to "
                    f"primitive type {primitive}"
                ) from coerce_error

        def lte(tpl1: Tuple[int, int], tpl2: Tuple[int, int]) -> bool:
            return tpl1[0] <= tpl2[0] and tpl1[1] <= tpl2[1]

        if issubclass(primitive, int):
            is_flag = issubclass(enum, Flag)
            min_value = min(
                (
                    val if isinstance(val, primitive) else primitive(val)
                    for val in values(enum)
                    if val is not None
                )
            )
            max_value = max(
                (
                    val if isinstance(val, primitive) else primitive(val)
                    for val in values(enum)
                    if val is not None
                )
            )
            min_bits = (min_value.bit_length(), max_value.bit_length())

            if bit_length is not None:
                assert lte(min_bits, (bit_length, bit_length)), (
                    f"bit_length {bit_length} is too small to store all "
                    f"values of {enum}"
                )
                min_bits = (bit_length, bit_length)
            else:
                bit_length = max(min_bits)

            field_cls: Type[EnumField]
            if min_value < 0:
                # Its possible to create a flag enum with negative values. This
                # enum behaves like a regular enum - the bitwise combinations
                # do not work - these weird flag enums are supported as normal
                # enumerations with negative values at the DB level
                if lte(min_bits, (16, 15)):
                    field_cls = EnumSmallIntegerField
                elif lte(min_bits, (32, 31)):
                    field_cls = EnumIntegerField
                elif lte(min_bits, (64, 63)):
                    field_cls = EnumBigIntegerField
                else:
                    field_cls = EnumExtraBigIntegerField
            else:
                if min_bits[1] >= 64 and is_flag:
                    field_cls = (
                        ExtraBigIntegerFlagField
                        if is_flag
                        else EnumExtraBigIntegerField
                    )
                elif min_bits[1] >= 32:
                    field_cls = (
                        BigIntegerFlagField if is_flag else EnumPositiveBigIntegerField
                    )
                elif min_bits[1] >= 16:
                    field_cls = (
                        IntegerFlagField if is_flag else EnumPositiveIntegerField
                    )
                else:
                    field_cls = (
                        SmallIntegerFlagField
                        if is_flag
                        else EnumPositiveSmallIntegerField
                    )

            return field_cls(
                enum=enum, primitive=primitive, bit_length=bit_length, **field_kwargs
            )

        if issubclass(primitive, float):
            return EnumFloatField(enum=enum, primitive=primitive, **field_kwargs)

        if issubclass(primitive, str):
            return EnumCharField(enum=enum, primitive=primitive, **field_kwargs)

        if issubclass(primitive, datetime):
            return EnumDateTimeField(enum=enum, primitive=primitive, **field_kwargs)

        if issubclass(primitive, date):
            return EnumDateField(enum=enum, primitive=primitive, **field_kwargs)

        if issubclass(primitive, timedelta):
            return EnumDurationField(enum=enum, primitive=primitive, **field_kwargs)

        if issubclass(primitive, time):
            return EnumTimeField(enum=enum, primitive=primitive, **field_kwargs)

        if issubclass(primitive, Decimal):
            return EnumDecimalField(enum=enum, primitive=primitive, **field_kwargs)

        raise NotImplementedError(
            f"EnumField does not support enumerations of primitive type " f"{primitive}"
        )


class EnumField(
    Generic[PrimitiveT],
    # why can't mypy handle the dynamic base class below?
    with_typehint(Field),  # type: ignore
    metaclass=EnumFieldFactory,
):
    """
    This mixin class turns any Django database field into an enumeration field.
    It works by overriding validation and pre/post database hooks to validate
    and convert any values to the Enumeration type in question.

    :param enum: The enum class
    :param strict: If True (default) the field will throw ValueErrors if the
        value is not coercible to a valid enumeration type.
    :param coerce: If True (default) the field will always coerce values to the
        enum type when possible. If False, the field will contain the primitive
        type of the enumeration.
    :param constrained: If True (default) and strict is also true
        CheckConstraints will be added to the model to constrain values of the
        database column to values of the enumeration type. If True and strict
        is False constraints will still be added.
    :param args: Any standard unnamed field arguments for the underlying
        field type.
    :param field_kwargs: Any standard named field arguments for the underlying
        field type.
    """

    _enum_: Optional[Type[Enum]] = None
    _strict_: bool = True
    _coerce_: bool = True
    _primitive_: Optional[PrimitiveT] = None
    _value_primitives_: List[Any] = []
    _constrained_: bool = _strict_

    descriptor_class = ToPythonDeferredAttribute

    default_error_messages: Any = {  # mypy is stupid
        "invalid_choice": _("Value %(value)r is not a valid %(enum)r.")
    }

    # use properties to disable setters
    @property
    def enum(self):
        """The enumeration type"""
        return self._enum_

    @property
    def strict(self):
        """True if the field requires values to be valid enumeration values"""
        return self._strict_

    @property
    def coerce(self):
        """
        False if the field should not coerce values to the enumeration
        type
        """
        return self._coerce_

    @property
    def constrained(self):
        """
        False if the database values are not constrained to the enumeration.
        By default this is set to the value of strict.
        """
        return self._constrained_

    @property
    def primitive(self):
        """
        The most appropriate primitive non-Enumeration type that can represent
        all enumeration values. Deriving classes should return their canonical
        primitive type if this type is None. The reason for this is that the
        primitive type of an enumeration might be a derived class of the
        canonical primitive type (e.g. str or int), but this primitive type
        will not always be available - for instance in migration code.
        Migration code should only ever deal with the most basic python types
        to reduce the dependency footprint on externally defined code - in all
        but the weirdest cases this will work.
        """
        return self._primitive_

    def _coerce_to_value_type(self, value: Any) -> Any:
        """Coerce the value to the enumerations value type"""
        # note if enum type is int and a floating point is passed we could get
        # situations like X.xxx == X - this is acceptable
        if (
            value is not None
            and self.primitive
            and not isinstance(value, self.primitive)
        ):
            return self.primitive(value)
        return value

    def __init__(
        self,
        enum: Optional[Type[Enum]] = None,
        primitive: Optional[PrimitiveT] = None,
        strict: bool = _strict_,
        coerce: bool = _coerce_,
        constrained: Optional[bool] = None,
        **kwargs,
    ):
        self._enum_ = enum
        self._primitive_ = primitive
        self._value_primitives_ = [self._primitive_]
        for value_type in [type(value) for value in values(enum)]:
            if value_type not in self._value_primitives_:
                self._value_primitives_.append(value_type)
        self._strict_ = strict if enum else False
        self._coerce_ = coerce if enum else False
        self._constrained_ = constrained if constrained is not None else strict
        if self.enum is not None:
            kwargs.setdefault("choices", choices(enum))
        super().__init__(
            null=kwargs.pop("null", False) or None in values(self.enum), **kwargs
        )

    def __copy__(self):
        """
        See django.db.models.fields.Field.__copy__, we have to override this
        here because base implementation results in an "object layout differs
        from base" TypeError - we inherit a new Empty type from this instance's
        class to ensure the same object layout and then use the same "weird"
        copy mechanism as Django's base Field class. Django's Field class
        should probably use this same technique.
        """
        obj = type("Empty", (self.__class__,), {})()
        obj.__class__ = self.__class__
        obj.__dict__ = self.__dict__.copy()
        return obj

    def _fallback(self, value: Any) -> Any:
        """Allow deriving classes to implement a final fallback coercion attempt."""
        return value

    def _try_coerce(self, value: Any, force: bool = False) -> Union[Enum, Any]:
        """
        Attempt coercion of value to enumeration type instance, if unsuccessful
        and non-strict, coercion to enum's primitive type will be done,
        otherwise a ValueError is raised.
        """
        if self.enum is None:
            return value

        if (self.coerce or force) and not isinstance(value, self.enum):
            try:
                value = self.enum(value)
            except (TypeError, ValueError):
                try:
                    # value = self.primitive(value)
                    value = self._coerce_to_value_type(value)
                    value = self.enum(value)
                except (TypeError, ValueError, DecimalException):
                    try:
                        value = self.enum[value]
                    except KeyError as err:
                        if len(self._value_primitives_) > 1:
                            for primitive in self._value_primitives_:
                                try:
                                    return self.enum(primitive(value))
                                except Exception:
                                    pass
                        value = self._fallback(value)
                        if not isinstance(value, self.enum) and (
                            self.strict or not isinstance(value, self.primitive)
                        ):
                            raise ValueError(
                                f"'{value}' is not a valid "
                                f"{self.enum.__name__} required by field "
                                f"{self.name}."
                            ) from err

        elif not self.coerce:
            try:
                return self._coerce_to_value_type(value)
            except (TypeError, ValueError, DecimalException) as err:
                raise ValueError(
                    f"'{value}' is not a valid {self.primitive.__name__} "
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
            kwargs["choices"] = choices(self.enum)

        if "db_default" in kwargs:
            try:
                kwargs["db_default"] = getattr(
                    self.to_python(kwargs["db_default"]), "value", kwargs["db_default"]
                )
            except ValidationError:
                pass

        if "default" in kwargs:
            # ensure default in deconstructed fields is always the primitive
            # value type
            kwargs["default"] = getattr(self.get_default(), "value", self.get_default())

        return name, path, args, kwargs

    def get_prep_value(self, value: Any) -> Any:
        """
        Convert the database field value into the Enum type.

        See get_prep_value_
        """
        value = Field.get_prep_value(self, value)
        if self.enum:
            try:
                value = self._try_coerce(value, force=True)
                if isinstance(value, self.enum):
                    value = value.value
            except (ValueError, TypeError):
                if value is not None:
                    raise
        return value

    def get_db_prep_value(self, value, connection, prepared=False) -> Any:
        """
        Convert the field value into the Enum type and then pull its value
        out.

        See get_db_prep_value_
        """
        if not prepared:
            value = self.get_prep_value(value)
        return self._coerce_to_value_type(value)

    def from_db_value(
        self,
        value: Any,
        expression,
        connection,
    ) -> Any:
        """
        Convert the database field value into the Enum type.

        See from_db_value_
        """
        # give the super class converter a first whack if it exists
        value = getattr(super(), "from_db_value", lambda v: v)(value)
        try:
            return self._try_coerce(value)
        except (ValueError, TypeError):
            # oracle returns '' for null values sometimes ?? even though empty
            # strings are converted to nulls in Oracle ??
            value = None if value == "" and self.null and self.strict else value
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
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={
                    "value": value,
                    "enum": self.enum.__name__ if self.enum else "",
                },
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

    def validate(self, value: Any, model_instance: Optional[Model]):
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
            if err.code != "invalid_choice":
                raise err
        try:
            self._try_coerce(value, force=True)
        except ValueError as err:
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={
                    "value": value,
                    "enum": self.enum.__name__ if self.enum else "",
                },
            ) from err

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        # super().formfield deletes anything unrecognized from kwargs that
        #   we try to pass in. Very annoying because we have to
        #   un-encapsulate some of this initialization logic, this makes our
        #   EnumChoiceField pretty ugly!

        is_multi = self.enum and issubclass(self.enum, Flag)
        if is_multi and self.enum:
            kwargs["empty_value"] = self.enum(0)
            # why fail? - does this fail for single select too?
            # kwargs['show_hidden_initial'] = True

        if not self.strict:
            kwargs.setdefault(
                "widget", NonStrictSelectMultiple if is_multi else NonStrictSelect
            )
        elif is_multi:
            kwargs.setdefault("widget", FlagSelectMultiple)

        form_field = super().formfield(
            form_class=form_class,
            choices_form_class=(
                choices_form_class or EnumFlagField if is_multi else EnumChoiceField
            ),
            **kwargs,
        )

        # we can't pass these in kwargs because formfield() strips them out
        form_field.enum = self.enum
        form_field.strict = self.strict
        form_field.primitive = self.primitive
        return form_field

    def get_choices(
        self,
        include_blank=True,
        blank_choice=tuple(BLANK_CHOICE_DASH),
        limit_choices_to=None,
        ordering=(),
    ):
        if self.enum and issubclass(self.enum, Flag):
            blank_choice = [(self.enum(0), "---------")]
        return [
            (getattr(choice, "value", choice), label)
            for choice, label in super().get_choices(
                include_blank=include_blank,
                blank_choice=list(blank_choice),
                limit_choices_to=limit_choices_to,
                ordering=ordering,
            )
        ]

    @staticmethod
    def constraint_name(
        model_class: Type[Model], field_name: str, enum: Type[Enum]
    ) -> str:
        """
        Get a check constraint name for the given enumeration field on the
        given model class. Check constraint names are limited to
        MAX_CONSTRAINT_NAME_LENGTH. The beginning parts of the name will be
        chopped off if it is too long.

        :param model_class: The class of the Model the field is on
        :param field_name: The name of the field
        :param enum: The enumeration type of the EnumField
        """
        name = (
            f"{model_class._meta.app_label}_"
            f"{model_class.__name__}_{field_name}_"
            f"{enum.__name__}"
        )
        while len(name) > MAX_CONSTRAINT_NAME_LENGTH:
            return name[len(name) - MAX_CONSTRAINT_NAME_LENGTH :]
        return name

    def contribute_to_class(
        self, cls: Type[Model], name: str, private_only: bool = False
    ):
        super().contribute_to_class(cls, name, private_only=private_only)
        if self.constrained and self.enum and issubclass(self.enum, IntFlag):
            # It's possible to declare an IntFlag field with negative values -
            # these enums do not behave has expected and flag-like DB
            # operations are not supported, so they are treated as normal
            # IntEnum fields, but the check constraints are flag-like range
            # constraints, so we bring those in here
            FlagField.contribute_to_class(self, cls, name, private_only=private_only)
        elif self.constrained and self.enum:
            constraint = Q(
                **{
                    f"{name}__in": [
                        self._coerce_to_value_type(value) for value in values(self.enum)
                    ]
                }
            )
            if self.null:
                constraint |= Q(**{f"{name}__isnull": True})
            cls._meta.constraints = [
                *cls._meta.constraints,
                CheckConstraint(
                    **{  # type: ignore[arg-type]
                        condition: constraint,
                        "name": self.constraint_name(cls, name, self.enum),
                    }
                ),
            ]
            # this dictionary is used to serialize the model, so if constraints
            # is not present - they will not be added to migrations
            cls._meta.original_attrs.setdefault(
                "constraints",
                cls._meta.constraints,
            )


class EnumCharField(EnumField[Type[str]], CharField):
    """
    A database field supporting enumerations with character values.
    """

    empty_values = [empty for empty in CharField.empty_values if empty != ""]

    @property
    def primitive(self):
        return EnumField.primitive.fget(self) or str  # type: ignore

    def __init__(
        self,
        enum: Optional[Type[Enum]] = None,
        primitive: Optional[Type[str]] = str,
        **kwargs,
    ):
        self._enum_ = enum
        self._primitive_ = primitive
        if self.enum:
            kwargs.setdefault(
                "max_length",
                max(
                    (
                        len(self._coerce_to_value_type(choice[0]) or "")
                        for choice in kwargs.get("choices", choices(enum))
                    )
                ),
            )
        super().__init__(enum=enum, primitive=primitive, **kwargs)


class EnumFloatField(EnumField[Type[float]], FloatField):
    """A database field supporting enumerations with floating point values"""

    _tolerance_: float
    _value_primitives_: List[Tuple[float, Enum]]

    @property
    def primitive(self):
        return EnumField.primitive.fget(self) or float  # type: ignore

    def _fallback(self, value: Any) -> Any:
        if value and isinstance(value, float):
            for en_value, en in self._value_primitives_:
                if abs(en_value - value) < self._tolerance_:
                    return en
        return value

    def __init__(
        self,
        enum: Optional[Type[Enum]] = None,
        primitive: Optional[Type[float]] = None,
        strict: bool = EnumField._strict_,
        coerce: bool = EnumField._coerce_,
        constrained: Optional[bool] = None,
        **kwargs,
    ):
        super().__init__(
            enum=enum,
            primitive=primitive,
            strict=strict,
            coerce=coerce,
            constrained=constrained,
            **kwargs,
        )
        # some database backends (earlier supported versions of Postgres)
        # can't rely on straight equality because of floating point imprecision
        if self.enum:
            self._value_primitives_ = []
            for en in self.enum:
                if en.value is not None:
                    self._value_primitives_.append(
                        (self._coerce_to_value_type(en.value), en)
                    )
            self._tolerance_ = (
                min((prim[0] * 1e-6 for prim in self._value_primitives_))
                if self._value_primitives_
                else 0.0
            )


class IntEnumField(EnumField[Type[int]]):
    """
    A mixin containing common implementation details for a database field
    supporting enumerations with integer values.
    """

    @property
    def bit_length(self):
        """
        The minimum number of bits required to represent all primitive values
        of the enumeration
        """
        return self._bit_length_

    @property
    def primitive(self):
        """
        The common primitive type of the enumeration values. This will always
        be int or a subclass of int.
        """
        return EnumField.primitive.fget(self) or int  # type: ignore

    def __init__(
        self,
        enum: Optional[Type[Enum]] = None,
        primitive: Optional[Type[int]] = int,
        bit_length: Optional[int] = None,
        **kwargs,
    ):
        self._bit_length_ = bit_length
        super().__init__(enum=enum, primitive=primitive, **kwargs)


class EnumSmallIntegerField(IntEnumField, SmallIntegerField):
    """
    A database field supporting enumerations with integer values that fit into
    2 bytes or fewer
    """


class EnumPositiveSmallIntegerField(IntEnumField, PositiveSmallIntegerField):
    """
    A database field supporting enumerations with positive (but signed) integer
    values that fit into 2 bytes or fewer
    """


class EnumIntegerField(IntEnumField, IntegerField):
    """
    A database field supporting enumerations with integer values that fit into
    32 bytes or fewer
    """


class EnumPositiveIntegerField(IntEnumField, PositiveIntegerField):
    """
    A database field supporting enumerations with positive (but signed) integer
    values that fit into 32 bytes or fewer
    """


class EnumBigIntegerField(IntEnumField, BigIntegerField):
    """
    A database field supporting enumerations with integer values that fit into
    64 bytes or fewer
    """


class EnumPositiveBigIntegerField(IntEnumField, PositiveBigIntegerField):
    """
    A database field supporting enumerations with positive (but signed) integer
    values that fit into 64 bytes or fewer
    """


class EnumDateField(EnumField[Type[date]], DateField):
    """
    A database field supporting enumerations with date values.
    """

    @property
    def primitive(self):
        return EnumField.primitive.fget(self) or date  # type: ignore

    def to_python(self, value: Any) -> Union[Enum, Any]:
        if not self.enum:
            return DateField.to_python(self, value)
        if not isinstance(value, self.enum):
            value = DateField.to_python(self, value)
        return EnumField.to_python(self, value)

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        val = val.value if isinstance(val, Enum) else val
        return "" if val is None else val.isoformat()

    def get_db_prep_value(self, value, connection, prepared=False) -> Any:
        return DateField.get_db_prep_value(
            self,
            (
                super().get_db_prep_value(value, connection, prepared=prepared)
                if not prepared
                else value
            ),
            connection=connection,
            prepared=True,
        )


class EnumDateTimeField(EnumField[Type[datetime]], DateTimeField):
    """
    A database field supporting enumerations with datetime values.
    """

    @property
    def primitive(self):
        return EnumField.primitive.fget(self) or datetime  # type: ignore

    def to_python(self, value: Any) -> Union[Enum, Any]:
        if not self.enum:
            return DateTimeField.to_python(self, value)
        if not isinstance(value, self.enum):
            value = DateTimeField.to_python(self, value)
        return EnumField.to_python(self, value)

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        val = val.value if isinstance(val, Enum) else val
        return "" if val is None else val.isoformat()

    def get_db_prep_value(self, value, connection, prepared=False) -> Any:
        return DateTimeField.get_db_prep_value(
            self,
            (
                super().get_db_prep_value(value, connection, prepared=prepared)
                if not prepared
                else value
            ),
            connection=connection,
            prepared=True,
        )


class EnumDurationField(EnumField[Type[timedelta]], DurationField):
    """
    A database field supporting enumerations with duration values.
    """

    @property
    def primitive(self):
        return EnumField.primitive.fget(self) or timedelta  # type: ignore

    def to_python(self, value: Any) -> Union[Enum, Any]:
        if not self.enum:
            return DurationField.to_python(self, value)
        if not isinstance(value, self.enum):
            value = DurationField.to_python(self, value)
        return EnumField.to_python(self, value)

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        val = val.value if isinstance(val, Enum) else val
        return "" if val is None else duration_string(val)

    def get_db_prep_value(self, value, connection, prepared=False) -> Any:
        return DurationField.get_db_prep_value(
            self,
            (
                super().get_db_prep_value(value, connection, prepared=prepared)
                if not prepared
                else value
            ),
            connection=connection,
            prepared=True,
        )


class EnumTimeField(EnumField[Type[time]], TimeField):
    """
    A database field supporting enumerations with time values.
    """

    @property
    def primitive(self):
        return EnumField.primitive.fget(self) or time  # type: ignore

    def to_python(self, value: Any) -> Union[Enum, Any]:
        if not self.enum:
            return TimeField.to_python(self, value)
        if not isinstance(value, self.enum):
            value = TimeField.to_python(self, value)
        return EnumField.to_python(self, value)

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        val = val.value if isinstance(val, Enum) else val
        return "" if val is None else val.isoformat()

    def get_db_prep_value(self, value, connection, prepared=False) -> Any:
        return TimeField.get_db_prep_value(
            self,
            (
                super().get_db_prep_value(value, connection, prepared=prepared)
                if not prepared
                else value
            ),
            connection=connection,
            prepared=True,
        )


class EnumDecimalField(EnumField[Type[Decimal]], DecimalField):
    """
    A database field supporting enumerations with Decimal values.
    """

    @property
    def primitive(self):
        return EnumField.primitive.fget(self) or Decimal  # type: ignore

    def __init__(
        self,
        enum: Optional[Type[Enum]] = None,
        primitive: Optional[Type[Decimal]] = None,
        max_digits: Optional[int] = None,
        decimal_places: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(
            enum=enum,
            primitive=primitive,
            **{
                **kwargs,
                **decimal_params(
                    enum, max_digits=max_digits, decimal_places=decimal_places
                ),
            },
        )

    def to_python(self, value: Any) -> Union[Enum, Any]:
        if not self.enum:
            return DecimalField.to_python(self, value)
        if not isinstance(value, self.enum):
            value = DecimalField.to_python(self, value)
        return EnumField.to_python(self, value)

    @cached_property
    def validators(self):
        return [
            (
                EnumValidatorAdapter(validator)  # type: ignore
                if isinstance(validator, DecimalValidator)
                else validator
            )
            for validator in super().validators
        ]

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        val = val.value if isinstance(val, Enum) else val
        return "" if val is None else str(val)

    def get_db_prep_save(self, value, connection):
        """Override base class to avoid calling to_python() in Django < 4."""
        return self.get_db_prep_value(value, connection)

    def get_prep_value(self, value: Any) -> Any:
        """By-pass base class - it calls to_python() which we don't want."""
        return EnumField.get_prep_value(self, value)

    def get_db_prep_value(self, value, connection, prepared=False) -> Any:
        if not prepared:
            value = self._coerce_to_value_type(self.get_prep_value(value))
        return connection.ops.adapt_decimalfield_value(value)


class FlagField(with_typehint(IntEnumField)):  # type: ignore
    """
    A common base class for EnumFields that store Flag enumerations and
    support bitwise operations.
    """

    enum: Type[Flag]

    def contribute_to_class(
        self, cls: Type[Model], name: str, private_only: bool = False
    ) -> None:
        """
        Add check constraints that honor flag fields range and boundary
        setting. Bypass EnumField's contribute_to_class() method, which adds
        constraints that are too specific.

        Boundary settings:
            "strict" -> error is raised  [default for Flag]
            "conform" -> extra bits are discarded
            "eject" -> lose flag status [default for IntFlag]
            "keep" -> keep flag status and all bits

        The constraints here are designed to make sense given the boundary
        setting, ensure that simple database reads through the ORM cannot throw
        exceptions and that search behaves as expected.

        - KEEP: no constraints
        - EJECT: constrained to the enum's range if strict is True
        - CONFORM: constrained to the enum's range. It would be possible to
            insert and load an out of range value, but that value would not be
            searchable so a constraint is added.
        - STRICT: constrained to the enum's range

        """
        if self.constrained and self.enum and self.bit_length <= 64:
            boundary = getattr(self.enum, "_boundary_", None)
            is_conform, is_eject, is_strict = (
                boundary is CONFORM,
                boundary is EJECT,
                boundary is STRICT,
            )

            flags = [
                self._coerce_to_value_type(val)
                for val in values(self.enum)
                if val is not None
            ]

            if is_strict or is_conform or (is_eject and self.strict) and flags:
                constraint = (
                    Q(**{f"{name}__gte": min(*flags)})
                    & Q(**{f"{name}__lte": reduce(or_, flags)})
                ) | Q(**{name: 0})

                if self.null:
                    constraint |= Q(**{f"{name}__isnull": True})

                cls._meta.constraints = [
                    *cls._meta.constraints,
                    CheckConstraint(
                        **{
                            condition: constraint,
                            "name": self.constraint_name(cls, name, self.enum),
                        }
                    ),
                ]
                # this dictionary is used to serialize the model, so if
                # constraints is not present - they will not be added to
                # migrations
                cls._meta.original_attrs.setdefault(
                    "constraints",
                    cls._meta.constraints,
                )
        if isinstance(self, FlagField):
            # this may have been called by a normal EnumField to bring in flag-like constraints
            # for non flag fields
            IntegerField.contribute_to_class(self, cls, name, private_only=private_only)


class SmallIntegerFlagField(FlagField, EnumPositiveSmallIntegerField):
    """
    A database field supporting flag enumerations with positive integer values
    that fit into 2 bytes or fewer
    """


class IntegerFlagField(FlagField, EnumPositiveIntegerField):
    """
    A database field supporting flag enumerations with positive integer values
    that fit into 32 bytes or fewer
    """


class BigIntegerFlagField(FlagField, EnumPositiveBigIntegerField):
    """
    A database field supporting flag enumerations with integer values that fit
    into 64 bytes or fewer
    """


for field in [SmallIntegerFlagField, IntegerFlagField, BigIntegerFlagField]:
    field.register_lookup(HasAnyFlagsLookup)
    field.register_lookup(HasAllFlagsLookup)


class EnumExtraBigIntegerField(IntEnumField, BinaryField):
    """
    A database field supporting enumerations with integer values that require
    more than 64 bits. This field only works for Enums that inherit from int.
    This field stores enum values in big endian byte order.
    """

    description = _("A bit field wider than the standard word size.")

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
        value = int(getattr(value, "value", value))
        value = value.to_bytes(
            (value.bit_length() + 7) // 8, byteorder="big", signed=self.signed
        )
        return BinaryField.get_prep_value(self, value)

    def get_db_prep_value(self, value: Any, connection, prepared=False):
        """
        Convert the field value into the Enum type and then pull its value
        out.

        See get_db_prep_value_
        """
        if value is None or isinstance(value, (bytes, memoryview, bytearray)):
            return value

        value = self._try_coerce(value, force=True)
        value = int(getattr(value, "value", value))
        value = value.to_bytes(
            (value.bit_length() + 7) // 8, byteorder="big", signed=self.signed
        )
        return BinaryField.get_db_prep_value(self, value, connection, prepared)

    def from_db_value(
        self,
        value: Any,
        expression,
        connection,
    ) -> Any:
        """
        Convert the database field value into the Enum type.

        See from_db_value_
        """
        if value is None:
            return value
        return super().from_db_value(
            int.from_bytes(value, byteorder="big", signed=self.signed),
            expression,
            connection,
        )

    def contribute_to_class(self, cls, name, private_only: bool = False):
        BinaryField.contribute_to_class(self, cls, name, private_only=private_only)


class ExtraBigIntegerFlagField(FlagField, EnumExtraBigIntegerField):
    """
    Flag fields that require more than 64 bits.
    """

    def contribute_to_class(self, cls, name, private_only: bool = False):
        BinaryField.contribute_to_class(self, cls, name, private_only=private_only)


# ExtraBigIntegerFlagField.register_lookup(HasAnyFlagsExtraBigLookup)
# ExtraBigIntegerFlagField.register_lookup(HasAllFlagsExtraBigLookup)
