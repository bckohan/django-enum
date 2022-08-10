from django.db.models import IntegerChoices, TextChoices
from django.db.models.enums import Choices


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
