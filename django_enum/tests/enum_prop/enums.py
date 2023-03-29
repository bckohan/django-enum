try:

    from django.db.models import IntegerChoices as DjangoIntegerChoices
    from django.db.models import TextChoices as DjangoTextChoices
    from django.utils.translation import gettext as _
    from django_enum import (
        FlagChoices,
        FloatChoices,
        IntegerChoices,
        TextChoices,
    )
    from enum_properties import p, s


    class DJIntEnum(DjangoIntegerChoices):

        ONE = 1, 'One'
        TWO = 2, 'Two'
        THREE = 3, 'Three'


    class DJTextEnum(DjangoTextChoices):

        A = 'A', 'Label A'
        B = 'B', 'Label B'
        C = 'C', 'Label C'


    class TextEnum(TextChoices, p('version'), p('help'), s('aliases', case_fold=True)):

        VALUE1 = 'V1', 'Value1', 0, _('Some help text about value1.'), ['val1', 'v1', 'v one']
        VALUE2 = 'V22', 'Value2', 1, _('Some help text about value2.'), {'val22', 'v2', 'v two'}
        VALUE3 = 'V333', 'Value3', 2, _('Some help text about value3.'), ['val333', 'v3', 'v three']
        DEFAULT = 'D', 'Default', 3, _('Some help text about default.'), {'default', 'defacto', 'none'}


    class Constants(FloatChoices, s('symbol')):

        PI = 3.14159265358979323846264338327950288, 'Pi', 'π'
        e = 2.71828, "Euler's Number", 'e'
        GOLDEN_RATIO = 1.61803398874989484820458683436563811, 'Golden Ratio', 'φ'


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


    class BigIntEnum(IntegerChoices, s('pos'), p('help')):

        VAL0 = -2147483649, 'Value -2147483649', BigPosIntEnum.VAL0, _('One less than the least regular integer.')
        VAL1 = 1, 'Value 1', BigPosIntEnum.VAL1, _('Something in the middle.')
        VAL2 = 2, 'Value 2', BigPosIntEnum.VAL2, _('Something in the middle.')
        VAL3 = 2147483648, 'Value 2147483648', BigPosIntEnum.VAL3, _('One more than the greatest regular integer.')


    class PrecedenceTest(
        s('prop1'),
        s('prop2'),
        IntegerChoices,
        s('prop3', case_fold=False),
        s('prop4', case_fold=True)
    ):
        P1 = 0, 'Precedence 1', 3, 0.1, _('First'), ['0.4', 'Fourth', 1]
        P2 = 1, 'Precedence 2', 2, 0.2, _('Second'), {'0.3', 'Third', 2}
        P3 = 2, 'Precedence 3', '1', 0.3, _('Third'), [0.2, 'Second', 3]
        P4 = 3, 'Precedence 4', 0, 0.4, _('Fourth'), {0.1, 'First', 4}


    class CarrierFrequency(FlagChoices, p('mhz')):

        L1   = 1, 1575.420
        L2   = 2, 1227.600
        L5   = 4, 1176.450

        G1   = 8, 1602.000
        G2  = 16, 1246.000

        E1  = 32, 1575.420
        E6  = 64, 1278.750
        E5  = 128, 1191.795
        E5a = 256, 1176.450
        E5b = 512, 1207.140

        B1 = 1024, 1561.100
        B2 = 2048, 1207.140
        B3 = 4096, 1268.520


    class GNSSConstellation(
        FlagChoices,
        s('country'),
        p('satellites'),
        p('frequencies')
    ):

        _symmetric_builtins_ = [s('label', case_fold=True)]

        GPS     = 1,  'USA',    31,  CarrierFrequency.L1 | CarrierFrequency.L2 | CarrierFrequency.L5
        GLONASS = 2,  'Russia', 24,  CarrierFrequency.G1 | CarrierFrequency.G2
        GALILEO = 4,  'EU',     30,  CarrierFrequency.E1 | CarrierFrequency.E5 | CarrierFrequency.E5a | CarrierFrequency.E5b | CarrierFrequency.E6
        BEIDOU  = 8,  'China',  30,  CarrierFrequency.B1 | CarrierFrequency.B2 | CarrierFrequency.B3
        QZSS    = 16, 'Japan',   7,  CarrierFrequency.L1 | CarrierFrequency.L2 | CarrierFrequency.L5

    class LargeBitField(FlagChoices):

        ONE = 2**0, 'One'
        TWO = 2**128, 'Two'

    class LargeNegativeField(IntegerChoices):

        NEG_ONE = -2**128, 'Negative One'
        ZERO = 0, 'Zero'

except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass
