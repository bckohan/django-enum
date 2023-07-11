import enum
from enum import IntFlag

from django.db import models
from django.db.models import TextChoices
from django.urls import reverse
from django_enum import EnumField
from django_enum.tests.djenum.enums import (
    BigIntEnum,
    BigNegativeFlagEnum,
    BigPosIntEnum,
    BigPositiveFlagEnum,
    Constants,
    DateEnum,
    DateTimeEnum,
    DecimalEnum,
    DJIntEnum,
    DJTextEnum,
    DurationEnum,
    ExternEnum,
    ExtraBigNegativeFlagEnum,
    ExtraBigPositiveFlagEnum,
    IntEnum,
    NegativeFlagEnum,
    PosIntEnum,
    PositiveFlagEnum,
    SmallIntEnum,
    SmallNegativeFlagEnum,
    SmallPosIntEnum,
    SmallPositiveFlagEnum,
    TextEnum,
    TimeEnum,
)


class EnumTester(models.Model):

    small_pos_int = EnumField(SmallPosIntEnum, null=True, default=None, db_index=True, blank=True)
    small_int = EnumField(SmallIntEnum, null=False, default=SmallIntEnum.VAL3, db_index=True, blank=True)

    pos_int = EnumField(PosIntEnum, default=2147483647, db_index=True, blank=True)
    int = EnumField(IntEnum, null=True, db_index=True, blank=True)

    big_pos_int = EnumField(BigPosIntEnum, null=True, default=None, db_index=True, blank=True)
    big_int = EnumField(BigIntEnum, default=-2147483649, db_index=True, blank=True)

    constant = EnumField(Constants, null=True, default=None, db_index=True, blank=True)

    text = EnumField(TextEnum, null=True, default=None, db_index=True, blank=False)

    extern = EnumField(ExternEnum, null=True, default=None, db_index=True, blank=True)

    # basic choice fields - used to compare behavior
    int_choice = models.IntegerField(
        default=1,
        null=False,
        blank=True,
        choices=((1, 'One'), (2, 'Two'), (3, 'Three'))
    )

    char_choice = models.CharField(
        max_length=1,
        default='A',
        null=False,
        blank=True,
        choices=(('A', 'First'), ('B', 'Second'), ('C', 'Third'))
    )

    int_field = models.IntegerField(
        default=1,
        null=False,
        blank=True
    )

    float_field = models.FloatField(
        default=1.5,
        null=False,
        blank=True
    )

    char_field = models.CharField(
        max_length=1,
        default='A',
        null=False,
        blank=True
    )
    ################################################

    dj_int_enum = EnumField(DJIntEnum, default=DJIntEnum.ONE)
    dj_text_enum = EnumField(DJTextEnum, default='A')

    # Non-strict
    non_strict_int = EnumField(
        SmallPosIntEnum,
        strict=False,
        null=True,
        default=5,
        blank=True
    )

    non_strict_text = EnumField(
        TextEnum,
        max_length=12,
        strict=False,
        null=False,
        default='',
        blank=True
    )

    no_coerce = EnumField(
        SmallPosIntEnum,
        coerce=False,
        null=True,
        default=None,
        blank=True
    )

    # exotics
    date_enum = EnumField(
        DateEnum,
        null=False,
        default=DateEnum.EMMA,
        blank=True,
        choices=[
            (DateEnum.EMMA, 'Emma'),
            (DateEnum.BRIAN, 'Brian'),
            (DateEnum.HUGO, 'Hugo')
        ]
    )
    datetime_enum = EnumField(
        DateTimeEnum,
        null=True,
        default=None,
        blank=True,
        strict=False
    )
    time_enum = EnumField(
        TimeEnum,
        null=True,
        default=None,
        blank=True
    )

    duration_enum = EnumField(
        DurationEnum,
        null=True,
        default=None,
        blank=True
    )

    decimal_enum = EnumField(
        DecimalEnum,
        null=False,
        default=DecimalEnum.THREE.value,
        blank=True,
        choices=[
            (DecimalEnum.ONE.value, 'One'),
            (DecimalEnum.TWO.value, 'Two'),
            (DecimalEnum.THREE.value, 'Three'),
            (DecimalEnum.FOUR.value, 'Four'),
            (DecimalEnum.FIVE.value, 'Five')
        ]
    )

    def get_absolute_url(self):
        return reverse('django_enum_tests_djenum:enum-detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ('id',)


class BadDefault(models.Model):

    # Non-strict
    non_strict_int = EnumField(
        SmallPosIntEnum,
        null=True,
        default=5,
        blank=True
    )


class AdminDisplayBug35(models.Model):

    text_enum = EnumField(
        DJTextEnum,
        null=True,
        default=None
    )

    int_enum = EnumField(
        DJIntEnum,
        null=True,
        default=None
    )


class EmptyEnumValueTester(models.Model):

    class BlankTextEnum(TextChoices):
        VALUE1 = '', 'Value1'
        VALUE2 = 'V22', 'Value2'

    class NoneIntEnum(enum.Enum):
        VALUE1 = None
        VALUE2 = 2

    blank_text_enum = EnumField(BlankTextEnum, default='')
    none_int_enum = EnumField(NoneIntEnum, null=True, default=None)

    # should not be possible to store NoneIntEnum.VALUE1
    none_int_enum_non_null = EnumField(NoneIntEnum, null=False)


class EnumFlagTester(models.Model):

    small_pos = EnumField(
        SmallPositiveFlagEnum,
        default=None,
        null=True,
        db_index=True,
        blank=True
    )

    pos = EnumField(
        PositiveFlagEnum,
        default=PositiveFlagEnum(0),
        db_index=True,
        blank=True
    )

    big_pos = EnumField(
        BigPositiveFlagEnum,
        default=BigPositiveFlagEnum(0),
        db_index=True,
        blank=True
    )

    extra_big_pos = EnumField(
        ExtraBigPositiveFlagEnum,
        default=ExtraBigPositiveFlagEnum(0),
        db_index=True,
        blank=True
    )

    small_neg = EnumField(
        SmallNegativeFlagEnum,
        default=SmallNegativeFlagEnum(0),
        db_index=True,
        blank=True
    )

    neg = EnumField(
        NegativeFlagEnum,
        default=NegativeFlagEnum(0),
        db_index=True,
        blank=True
    )

    big_neg = EnumField(
        BigNegativeFlagEnum,
        default=BigNegativeFlagEnum(0),
        db_index=True,
        blank=True
    )

    extra_big_neg = EnumField(
        ExtraBigNegativeFlagEnum,
        default=ExtraBigNegativeFlagEnum(0),
        db_index=True,
        blank=True
    )

    def __repr__(self):
        return f'EnumFlagTester(small_pos={repr(self.small_pos)}, ' \
               f'pos={repr(self.pos)}, ' \
               f'big_pos={repr(self.big_pos)}, ' \
               f'extra_big_pos={repr(self.extra_big_pos)}, ' \
               f'small_neg={repr(self.small_neg)}, neg={repr(self.neg)}, ' \
               f'big_neg={repr(self.big_neg)}, ' \
               f'extra_big_neg={repr(self.extra_big_neg)})'
