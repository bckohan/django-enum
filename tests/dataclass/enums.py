from datetime import date, datetime, time, timedelta
from decimal import Decimal
import typing as t

from django.db.models import IntegerChoices as DjangoIntegerChoices
from django.db.models import TextChoices as DjangoTextChoices
from enum import Enum
from django.utils.translation import gettext as _
from dataclasses import dataclass, is_dataclass, fields
import unicodedata

from tests.utils import try_convert


def casenorm(text: t.Any) -> t.Any:
    """Normalize unicode text to be case agnostic."""
    if isinstance(text, str):
        return unicodedata.normalize("NFKD", text.casefold())
    return text


class DJIntEnum(DjangoIntegerChoices):
    ONE = 1, "One"
    TWO = 2, "Two"
    THREE = 3, "Three"


class DJTextEnum(DjangoTextChoices):
    A = "A", "Label A"
    B = "B", "Label B"
    C = "C", "Label C"


class SymmetricMixin:
    __symmetric_values__ = ["label"]
    __isymmetric_values__ = []

    @classmethod
    def _missing_(cls, value):
        if not is_dataclass(cls):
            return super()._missing_(value)

        def matches(attr, case_fold):
            val_to_match = casenorm(value) if case_fold else value
            if isinstance(attr, (set, tuple, list)):
                for val in attr:
                    if case_fold:
                        if casenorm(val) == val_to_match:
                            return True
                    else:
                        if val == val_to_match:
                            return True
                return False
            return val_to_match == (casenorm(attr) if case_fold else attr)

        val_field = list(fields(cls))[0].name
        sym_vals: t.List[t.Tuple[str, bool]] = [
            (field.name, field.name in cls.__isymmetric_values__)
            for field in fields(cls)
            if field.name in cls.__symmetric_values__
            or field.name in cls.__isymmetric_values__
        ]
        if not sym_vals or val_field != sym_vals[0][0]:
            sym_vals.insert(0, (val_field, False))
        for field, case_fold in sym_vals:
            for member in cls:
                if matches(getattr(member, field), case_fold=case_fold):
                    return member
        return super()._missing_(value)


@dataclass(frozen=True, eq=True)
class TextEnumChoices:
    short: str
    label: str
    version: int
    help: str
    aliases: t.List[str]


class TextEnum(TextEnumChoices, SymmetricMixin, Enum):
    __symmetric_values__ = ["short", "label"]
    __isymmetric_values__ = ["aliases"]

    VALUE1 = (
        "V1",
        "Value1",
        0,
        _("Some help text about value1."),
        ["val1", "v1", "v one"],
    )
    VALUE2 = (
        "V22",
        "Value2",
        1,
        _("Some help text about value2."),
        ["val22", "v2", "v two"],
    )
    VALUE3 = (
        "V333",
        "Value3",
        2,
        _("Some help text about value3."),
        ["val333", "v3", "v three"],
    )
    DEFAULT = (
        "D",
        "Default",
        3,
        _("Some help text about default."),
        ["default", "defacto", "none"],
    )


@dataclass(frozen=True, eq=True)
class ConstantsChoices:
    constant: float
    label: str
    symbol: str


class Constants(ConstantsChoices, SymmetricMixin, Enum):
    __symmetric_values__ = ["constant", "label", "symbol"]

    PI = 3.14159265358979323846264338327950288, "Pi", "π"
    e = 2.71828, "Euler's Number", "e"
    GOLDEN_RATIO = 1.61803398874989484820458683436563811, "Golden Ratio", "φ"


@dataclass(frozen=True, eq=True)
class IntChoice:
    val: int
    label: str


class SmallPosIntEnum(IntChoice, SymmetricMixin, Enum):
    VAL1 = 0, "Value 1"
    VAL2 = 2, "Value 2"
    VAL3 = 32767, "Value 32767"


class SmallIntEnum(IntChoice, SymmetricMixin, Enum):
    VALn1 = -32768, "Value -32768"
    VAL0 = 0, "Value 0"
    VAL1 = 1, "Value 1"
    VAL2 = 2, "Value 2"
    VAL3 = 32767, "Value 32767"


class IntEnum(IntChoice, SymmetricMixin, Enum):
    VALn1 = -2147483648, "Value -2147483648"
    VAL0 = 0, "Value 0"
    VAL1 = 1, "Value 1"
    VAL2 = 2, "Value 2"
    VAL3 = 2147483647, "Value 2147483647"


class PosIntEnum(IntChoice, SymmetricMixin, Enum):
    VAL0 = 0, "Value 0"
    VAL1 = 1, "Value 1"
    VAL2 = 2, "Value 2"
    VAL3 = 2147483647, "Value 2147483647"


class BigPosIntEnum(IntChoice, SymmetricMixin, Enum):
    VAL0 = 0, "Value 0"
    VAL1 = 1, "Value 1"
    VAL2 = 2, "Value 2"
    VAL3 = 2147483648, "Value 2147483648"


@dataclass(frozen=True, eq=True)
class BigIntChoice:
    val: int
    label: str
    pos: BigPosIntEnum
    help: str


class BigIntEnum(BigIntChoice, SymmetricMixin, Enum):
    __symmetric_values__ = ["val", "label", "pos"]

    VAL0 = (
        -2147483649,
        "Value -2147483649",
        BigPosIntEnum.VAL0,
        _("One less than the least regular integer."),
    )
    VAL1 = 1, "Value 1", BigPosIntEnum.VAL1, _("Something in the middle.")
    VAL2 = 2, "Value 2", BigPosIntEnum.VAL2, _("Something in the middle.")
    VAL3 = (
        2147483648,
        "Value 2147483648",
        BigPosIntEnum.VAL3,
        _("One more than the greatest regular integer."),
    )


@dataclass(frozen=True, eq=True)
class DateChoice:
    day: date
    label: str


class DateEnum(DateChoice, SymmetricMixin, Enum):
    BRIAN = date(1984, 8, 7), "Brian"
    EMMA = date(1989, 7, 27), "Emma"
    HUGO = date(2016, 9, 9), "Hugo"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(try_convert(date, value, raise_on_error=True))
        return super()._missing_(value)

    def __eq__(self, other):
        if isinstance(other, str):
            try:
                return self == DateEnum(other)
            except ValueError:
                return False
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()


@dataclass(frozen=True, eq=True)
class DateTimeChoice:
    when: date
    label: str


class DateTimeEnum(DateTimeChoice, SymmetricMixin, Enum):
    ST_HELENS = datetime(1980, 5, 18, 8, 32, 0), "Mount St. Helens"
    PINATUBO = datetime(1991, 6, 15, 20, 9, 0), "Pinatubo"
    KATRINA = datetime(2005, 8, 29, 5, 10, 0), "Katrina"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(try_convert(datetime, value, raise_on_error=True))
        return super()._missing_(value)

    def __eq__(self, other):
        if isinstance(other, str):
            try:
                return self == DateTimeEnum(other)
            except ValueError:
                return False
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()


@dataclass(frozen=True, eq=True)
class TimeChoice:
    when: time
    label: str


class TimeEnum(TimeChoice, SymmetricMixin, Enum):
    COB = time(17, 0, 0), "Close of Business"
    LUNCH = time(12, 30, 0), "Lunch"
    MORNING = time(9, 0, 0), "Morning"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(try_convert(time, value, raise_on_error=True))
        return super()._missing_(value)

    def __eq__(self, other):
        if isinstance(other, str):
            try:
                return self == TimeEnum(other)
            except ValueError:
                return False
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()


@dataclass(frozen=True, eq=True)
class DurationChoice:
    duration: timedelta
    label: str


class DurationEnum(DurationChoice, SymmetricMixin, Enum):
    __isymmetric_values__ = ["label"]

    DAY = timedelta(days=1), "DAY"
    WEEK = timedelta(weeks=1), "WEEK"
    FORTNIGHT = timedelta(weeks=2), "FORTNIGHT"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(try_convert(timedelta, value, raise_on_error=True))
        return super()._missing_(value)

    def __eq__(self, other):
        if isinstance(other, str):
            try:
                return self == DurationEnum(other)
            except ValueError:
                return False
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()


@dataclass(frozen=True, eq=True)
class DecimalChoice:
    val: Decimal
    label: str


class DecimalEnum(DecimalChoice, SymmetricMixin, Enum):
    __isymmetric_values__ = ["label"]

    ONE = Decimal("0.99"), "One"
    TWO = Decimal("0.999"), "Two"
    THREE = Decimal("0.9999"), "Three"
    FOUR = Decimal("99.9999"), "Four"
    FIVE = Decimal("999"), "Five"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, (int, float, str)):
            return cls(try_convert(Decimal, value, raise_on_error=True))
        return super()._missing_(value)

    def __eq__(self, other):
        if isinstance(other, Decimal):
            return self.value == other
        if isinstance(other, str) and other or isinstance(other, (float, int)):
            try:
                return super().__eq__(DecimalEnum(str(other)))
            except ValueError:  # pragma: no cover
                return False
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()


@dataclass(frozen=True, eq=True)
class PrecedenceChoice:
    val: int
    label: str
    prop1: t.Union[str, int]
    prop2: float
    prop3: str
    prop4: t.List[t.Union[int, float, str]]


class PrecedenceTest(PrecedenceChoice, SymmetricMixin, Enum):
    __symmetric_values__ = ["label", "prop1", "prop2", "prop3"]
    __isymmetric_values__ = ["prop4"]

    P1 = 0, "Precedence 1", 3, 0.1, _("First"), ["0.4", "Fourth", 1]
    P2 = 1, "Precedence 2", 2, 0.2, _("Second"), ["0.3", "Third", 2]
    P3 = 2, "Precedence 3", "1", 0.3, _("Third"), [0.2, "Second", 3]
    P4 = 3, "Precedence 4", 0, 0.4, _("Fourth"), [0.1, "First", 4]


class ExternEnum(IntChoice, SymmetricMixin, Enum):
    """
    Tests that externally defined (i.e. not deriving from choices enums
    are supported.
    """

    __isymmetric_values__ = ["label"]

    ONE = 1, "One"
    TWO = 2, "Two"
    THREE = 3, "Three"
