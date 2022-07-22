from enum import auto

from django.db import models
from django.urls import reverse
from django_enum import EnumField, IntegerChoices, TextChoices
from django_enum.tests.app1.enums import (
    BigIntEnum,
    BigPosIntEnum,
    Constants,
    DJIntEnum,
    DJTextEnum,
    IntEnum,
    PosIntEnum,
    SmallIntEnum,
    SmallPosIntEnum,
    TextEnum,
)
from enum_properties import s


class EnumTester(models.Model):

    small_pos_int = EnumField(SmallPosIntEnum, null=True, default=None, db_index=True, blank=True)
    small_int = EnumField(SmallIntEnum, null=False, default=SmallIntEnum.VAL3, db_index=True, blank=True)

    pos_int = EnumField(PosIntEnum, default=PosIntEnum.VAL3, db_index=True, blank=True)
    int = EnumField(IntEnum, null=True, db_index=True, blank=True)

    big_pos_int = EnumField(BigPosIntEnum, null=True, default=None, db_index=True, blank=True)
    big_int = EnumField(BigIntEnum, default=BigIntEnum.VAL0, db_index=True, blank=True)

    constant = EnumField(Constants, null=True, default=None, db_index=True, blank=True)

    text = EnumField(TextEnum, null=True, default=None, db_index=True, blank=True)

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

    dj_int_enum = EnumField(DJIntEnum, default=DJIntEnum.ONE.value)
    dj_text_enum = EnumField(DJTextEnum, default=DJTextEnum.A.value)

    def get_absolute_url(self):
        return reverse('django_enum_tests_app1:enum-detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ('id',)


class MyModel(models.Model):

    class TextEnum(models.TextChoices):

        VALUE0 = 'V0', 'Value 0'
        VALUE1 = 'V1', 'Value 1'
        VALUE2 = 'V2', 'Value 2'

    class IntEnum(models.IntegerChoices):

        ONE   = 1, 'One'
        TWO   = 2, 'Two',
        THREE = 3, 'Three'

    class Color(TextChoices, s('rgb'), s('hex', case_fold=True)):
        # name   value   label       rgb       hex
        RED = 'R', 'Red', (1, 0, 0), 'ff0000'
        GREEN = 'G', 'Green', (0, 1, 0), '00ff00'
        BLUE = 'B', 'Blue', (0, 0, 1), '0000ff'

    txt_enum = EnumField(TextEnum, null=True, blank=True)
    int_enum = EnumField(IntEnum)
    color = EnumField(Color)

