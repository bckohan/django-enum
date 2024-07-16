"""
Support for Django model fields built from enumeration types.
"""
from enum import Enum
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

try:
    from django.db.models.expressions import DatabaseDefault
except ImportError:  # pragma: no cover
    class DatabaseDefault:  # type: ignore
        """Spoof DatabaseDefault for Django < 5.0"""

from django_enum.choices import choices, values
from django_enum.forms import EnumChoiceField, NonStrictSelect

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
            instance.__dict__[self.field.name] = (
                value
                if isinstance(value, DatabaseDefault) else
                self.field.to_python(value)
            )
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

    enum: Optional[Type[Enum]] = None
    strict: bool = True
    coerce: bool = True
    primitive: Type[Any]

    descriptor_class = ToPythonDeferredAttribute

    def __init__(
            self,
            *args,
            enum: Optional[Type[Enum]] = None,
            strict: bool = strict,
            coerce: bool = coerce,
            **kwargs
    ):
        self.enum = enum
        self.strict = strict if enum else False
        self.coerce = coerce if enum else False
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
        if self.enum is None:
            return value

        if (self.coerce or force) and not isinstance(value, self.enum):
            try:
                value = self.enum(value)
            except (TypeError, ValueError):
                try:
                    value = self.primitive(value)
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
                                f"{self.enum.__name__} "
                                f"required by field {self.name}."
                            ) from err
        elif (
            not self.coerce and
            not isinstance(value, self.primitive) and
            not isinstance(value, self.enum)
        ):
            try:
                return self.primitive(value)
            except (TypeError, ValueError) as err:
                raise ValueError(
                    f"'{value}' is not coercible to {self.primitive.__name__} "
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

        if 'db_default' in kwargs:
            try:
                kwargs['db_default'] = getattr(
                    self.to_python(kwargs['db_default']),
                    'value',
                    kwargs['db_default']
                )
            except ValidationError:
                pass

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
        if value is not None and self.enum is not None:
            value = self._try_coerce(value, force=True)
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
            value = self._try_coerce(value, force=True)
            if isinstance(value, self.enum):
                value = value.value
        return super().get_db_prep_value(
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
        return self._try_coerce(value)

    def to_python(self, value: Any) -> Union[Enum, Any]:
        """
        Converts the value in the enumeration type.

        See to_python_

        :param value: The value to convert
        :return: The converted value
        :raises ValidationError: If the value is not mappable to a valid
            enumeration
        """
        if value is None:
            return value

        try:
            return self._try_coerce(value)
        except ValueError as err:
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

        if not self.strict:
            kwargs.setdefault('widget', NonStrictSelect)

        form_field = super().formfield(
            form_class=form_class,
            choices_form_class=choices_form_class or EnumChoiceField,
            **kwargs
        )

        form_field.enum = self.enum
        form_field.strict = self.strict
        return form_field


class EnumCharField(EnumMixin, CharField):
    """
    A database field supporting enumerations with character values.
    """

    primitive = str

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

    primitive = float


class EnumSmallIntegerField(EnumMixin, SmallIntegerField):
    """
    A database field supporting enumerations with integer values that fit into
    2 bytes or fewer
    """

    primitive = int


class EnumPositiveSmallIntegerField(EnumMixin, PositiveSmallIntegerField):
    """
    A database field supporting enumerations with positive (but signed) integer
    values that fit into 2 bytes or fewer
    """

    primitive = int

class EnumIntegerField(EnumMixin, IntegerField):
    """
    A database field supporting enumerations with integer values that fit into
    32 bytes or fewer
    """

    primitive = int


class EnumPositiveIntegerField(EnumMixin, PositiveIntegerField):
    """
    A database field supporting enumerations with positive (but signed) integer
    values that fit into 32 bytes or fewer
    """

    primitive = int


class EnumBigIntegerField(EnumMixin, BigIntegerField):
    """
    A database field supporting enumerations with integer values that fit into
    64 bytes or fewer
    """

    primitive = int


class EnumPositiveBigIntegerField(EnumMixin, PositiveBigIntegerField):
    """
    A database field supporting enumerations with positive (but signed) integer
    values that fit into 64 bytes or fewer
    """

    primitive = int


class _EnumFieldMetaClass(type):

    SUPPORTED_PRIMITIVES = {int, str, float}

    def __new__(  # pylint: disable=R0911
            mcs,
            enum: Type[Enum]
    ) -> Type[EnumMixin]:
        """
        Construct a new Django Field class given the Enumeration class. The
        correct Django field class to inherit from is determined based on the
        primitive type seen in the Enumeration class's inheritance tree.

        :param enum: The class of the Enumeration to build a field class for
        """
        primitives = mcs.SUPPORTED_PRIMITIVES.intersection(set(enum.__mro__))
        primitive = (
            list(primitives)[0] if primitives else type(values(enum)[0])
        )
        assert primitive in mcs.SUPPORTED_PRIMITIVES, \
            f'Enum {enum} has values of an unnsupported primitive type: ' \
            f'{primitive}'

        if primitive is float:
            return EnumFloatField

        if primitive is int:
            vals = [define.value for define in enum]
            min_value = min(vals)
            max_value = max(vals)
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


def EnumField(  # pylint: disable=C0103
        enum: Type[Enum],
        *field_args,
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
    :param field_kwargs: Any standard named field arguments for the base
        field type.
    :return: An object of the appropriate enum field type
    """
    return _EnumFieldMetaClass(enum)(enum=enum, *field_args, **field_kwargs)
