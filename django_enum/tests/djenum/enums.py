from enum import IntEnum, Enum

from django.db.models import IntegerChoices, TextChoices
from django.db.models.enums import Choices
from datetime import date, datetime, time, timedelta
from decimal import Decimal


class FloatChoices(float, Choices):
    pass


class DJIntEnum(IntegerChoices):

    ONE = 1, 'One'
    TWO = 2, 'Two'
    THREE = 3, 'Three'


class DJTextEnum(TextChoices):

    A = 'A', 'Label A'
    B = 'B', 'Label B'
    C = 'C', 'Label C'


class TextEnum(TextChoices):

    VALUE1 = 'V1', 'Value1'
    VALUE2 = 'V22', 'Value2'
    VALUE3 = 'V333', 'Value3'
    DEFAULT = 'D', 'Default'


class ExternEnum(IntEnum):
    """
    Tests that externally defined (i.e. not deriving from choices enums
    are supported.
    """
    ONE   = 1
    TWO   = 2
    THREE = 3

    def __str__(self):
        return self.name


class Constants(FloatChoices):

    PI = 3.14159265358979323846264338327950288, 'Pi'
    e = 2.71828, "Euler's Number"
    GOLDEN_RATIO = 1.61803398874989484820458683436563811, 'Golden Ratio'


class SmallPosIntEnum(IntegerChoices):

    VAL1 = 0, 'Value 1'
    VAL2 = 2, 'Value 2'
    VAL3 = 32767, 'Value 32767'


class SmallIntEnum(IntegerChoices):

    VALn1 = -32768, 'Value -32768'
    VAL0 = 0, 'Value 0'
    VAL1 = 1, 'Value 1'
    VAL2 = 2, 'Value 2'
    VAL3 = 32767, 'Value 32767'


class IntEnum(IntegerChoices):

    VALn1 = -2147483648, 'Value -2147483648'
    VAL0 = 0, 'Value 0'
    VAL1 = 1, 'Value 1'
    VAL2 = 2, 'Value 2'
    VAL3 = 2147483647, 'Value 2147483647'


class PosIntEnum(IntegerChoices):

    VAL0 = 0, 'Value 0'
    VAL1 = 1, 'Value 1'
    VAL2 = 2, 'Value 2'
    VAL3 = 2147483647, 'Value 2147483647'


class BigPosIntEnum(IntegerChoices):

    VAL0 = 0, 'Value 0'
    VAL1 = 1, 'Value 1'
    VAL2 = 2, 'Value 2'
    VAL3 = 2147483648, 'Value 2147483648'


class BigIntEnum(IntegerChoices):

    VAL0 = -2147483649, 'Value -2147483649'
    VAL1 = 1, 'Value 1'
    VAL2 = 2, 'Value 2'
    VAL3 = 2147483648, 'Value 2147483648'


class DateEnum(Enum):

    BRIAN = date(1984, 8, 7)
    EMMA = date(1989, 7, 27)
    HUGO = date(2016, 9, 9)


class DateTimeEnum(Enum):

    ST_HELENS = datetime(1980, 5, 18, 8, 32, 0)
    PINATUBO = datetime(1991, 6, 15, 20, 9, 0)
    KATRINA = datetime(2005, 8, 29, 5, 10, 0)


class TimeEnum(Enum):

    COB = time(17, 0, 0)
    LUNCH = time(12, 30, 0)
    MORNING = time(9, 0, 0)


class DurationEnum(Enum):

    DAY = timedelta(days=1)
    WEEK = timedelta(weeks=1)
    FORTNIGHT = timedelta(weeks=2)


class DecimalEnum(Enum):

    ONE   = Decimal('0.99')
    TWO   = Decimal('0.999')
    THREE = Decimal('0.9999')
    FOUR  = Decimal('99.9999')
    FIVE  = Decimal('999')
