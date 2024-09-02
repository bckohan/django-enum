from django.db import models
from django.urls import reverse
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from django_enum import EnumField, TextChoices
from tests.dataclass.enums import (
    SymmetricMixin,
    IntChoice,
    BigIntEnum,
    BigPosIntEnum,
    Constants,
    DateEnum,
    DateTimeEnum,
    DecimalEnum,
    DJIntEnum,
    DJTextEnum,
    DurationEnum,
    ExternEnum,
    IntEnum,
    PosIntEnum,
    SmallIntEnum,
    SmallPosIntEnum,
    TextEnum,
    TimeEnum,
)


class EnumTester(models.Model):
    small_pos_int = EnumField(
        SmallPosIntEnum, null=True, default=None, db_index=True, blank=True
    )
    small_int = EnumField(
        SmallIntEnum, null=False, default="Value 32767", db_index=True, blank=True
    )

    pos_int = EnumField(PosIntEnum, default=2147483647, db_index=True, blank=True)
    int = EnumField(IntEnum, null=True, db_index=True, blank=True)

    big_pos_int = EnumField(
        BigPosIntEnum, null=True, default=None, db_index=True, blank=True
    )
    big_int = EnumField(
        BigIntEnum, default=BigPosIntEnum.VAL0, db_index=True, blank=True
    )

    constant = EnumField(Constants, null=True, default=None, db_index=True, blank=True)

    text = EnumField(TextEnum, null=True, default=None, db_index=True, blank=True)

    # eccentric enums
    date_enum = EnumField(DateEnum, null=False, default=DateEnum.EMMA, blank=True)

    datetime_enum = EnumField(
        DateTimeEnum, null=True, default=None, blank=True, strict=False
    )

    time_enum = EnumField(TimeEnum, null=True, default=None, blank=True)

    duration_enum = EnumField(DurationEnum, null=True, default=None, blank=True)

    decimal_enum = EnumField(
        DecimalEnum, null=False, default=DecimalEnum.THREE.value, blank=True
    )

    extern = EnumField(ExternEnum, null=True, default=None, db_index=True, blank=True)

    # basic choice fields - used to compare behavior
    int_choice = models.IntegerField(
        default=1,
        null=False,
        blank=True,
        choices=((1, "One"), (2, "Two"), (3, "Three")),
    )

    char_choice = models.CharField(
        max_length=50,
        default="A",
        null=False,
        blank=True,
        choices=(("A", "First"), ("B", "Second"), ("C", "Third")),
    )

    int_field = models.IntegerField(default=1, null=False, blank=True)

    float_field = models.FloatField(default=1.5, null=False, blank=True)

    char_field = models.CharField(max_length=1, default="A", null=False, blank=True)
    ################################################

    dj_int_enum = EnumField(DJIntEnum, default=DJIntEnum.ONE)
    dj_text_enum = EnumField(DJTextEnum, default=DJTextEnum.A)

    # Non-strict
    non_strict_int = EnumField(
        SmallPosIntEnum, strict=False, null=True, default=5, blank=True
    )
    non_strict_text = EnumField(
        TextEnum, max_length=12, strict=False, null=False, default="", blank=True
    )

    no_coerce = EnumField(
        SmallPosIntEnum, coerce=False, null=True, default=None, blank=True
    )

    def get_absolute_url(self):
        return reverse("tests_dataclass:enum-detail", kwargs={"pk": self.pk})

    class Meta:
        ordering = ("id",)
        # constraints = []


class MyModel(models.Model):
    @dataclass(frozen=True)
    class StrChoice:
        val: str
        label: str

    class TextEnum(StrChoice, SymmetricMixin, Enum):
        VALUE0 = "V0", "Value 0"
        VALUE1 = "V1", "Value 1"
        VALUE2 = "V2", "Value 2"

    class IntEnum(IntChoice, SymmetricMixin, Enum):
        ONE = 1, "One"
        TWO = (
            2,
            "Two",
        )
        THREE = 3, "Three"

    @dataclass(frozen=True)
    class ColorChoice:
        val: str
        label: str
        rgb: Tuple[int, int, int]
        hex: str

    class Color(ColorChoice, SymmetricMixin, Enum):
        __symmetric_values__ = ["val", "label", "rgb"]
        __isymmetric_values__ = ["hex"]

        # name   value   label       rgb       hex
        RED = "R", "Red", (1, 0, 0), "ff0000"
        GREEN = "G", "Green", (0, 1, 0), "00ff00"
        BLUE = "B", "Blue", (0, 0, 1), "0000ff"

    txt_enum = EnumField(TextEnum, null=True, blank=True)
    int_enum = EnumField(IntEnum)
    color = EnumField(Color)


class AdminDisplayBug35(models.Model):
    text_enum = EnumField(TextEnum, default=TextEnum.VALUE1)

    int_enum = EnumField(SmallPosIntEnum, default=SmallPosIntEnum.VAL2)

    blank_int = EnumField(SmallPosIntEnum, null=True, default=None)

    blank_txt = EnumField(TextEnum, null=True, default=None)
