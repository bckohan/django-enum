from django.db import models
from django.db.models.expressions import Value, F
from django.db.models.functions import Concat
from django.urls import reverse

from django_enum import EnumField
from tests.djenum.enums import (
    BigIntEnum,
    BigPosIntEnum,
    Constants,
    DJIntEnum,
    DJTextEnum,
    ExternEnum,
    IntEnum,
    PosIntEnum,
    SmallIntEnum,
    SmallPosIntEnum,
    TextEnum,
)


class DBDefaultTester(models.Model):
    small_pos_int = EnumField(SmallPosIntEnum, null=True, db_default=None, blank=True)
    small_int = EnumField(
        SmallIntEnum, null=False, db_default=SmallIntEnum.VAL3, blank=True
    )

    small_int_shadow = EnumField(
        SmallIntEnum, null=False, db_default=Value(SmallIntEnum.VAL3.value), blank=True
    )

    pos_int = EnumField(PosIntEnum, db_default=2147483647, blank=True)
    int = EnumField(IntEnum, null=True, db_default=IntEnum.VALn1, blank=True)

    big_pos_int = EnumField(BigPosIntEnum, null=True, db_default=None, blank=True)
    big_int = EnumField(BigIntEnum, db_default=-2147483649, blank=True)

    constant = EnumField(
        Constants, null=True, db_default=Constants.GOLDEN_RATIO, blank=True
    )

    text = EnumField(TextEnum, db_default="", blank=True, strict=False)
    doubled_text = EnumField(
        TextEnum,
        default="",
        db_default=Concat(Value("db"), Value("_default")),
        blank=True,
        max_length=10,
        strict=False,
    )
    doubled_text_strict = EnumField(
        TextEnum,
        default=TextEnum.DEFAULT,
        db_default=TextEnum.VALUE2,
        blank=True,
        max_length=10,
    )

    char_field = models.CharField(db_default="db_default", blank=True, max_length=10)
    doubled_char_field = models.CharField(
        default="default", db_default="db_default", blank=True, max_length=10
    )

    extern = EnumField(ExternEnum, null=True, db_default=ExternEnum.THREE, blank=True)

    dj_int_enum = EnumField(DJIntEnum, db_default=DJIntEnum.ONE)
    dj_text_enum = EnumField(DJTextEnum, db_default="A")

    # Non-strict
    non_strict_int = EnumField(
        SmallPosIntEnum, strict=False, null=True, db_default=5, blank=True
    )

    non_strict_text = EnumField(
        TextEnum,
        max_length=12,
        strict=False,
        null=False,
        db_default="arbitrary",
        blank=True,
    )

    no_coerce = EnumField(
        SmallPosIntEnum,
        coerce=False,
        null=True,
        db_default=SmallPosIntEnum.VAL2,
        blank=True,
    )

    no_coerce_value = EnumField(
        SmallPosIntEnum,
        coerce=False,
        null=True,
        db_default=SmallPosIntEnum.VAL3.value,
        blank=True,
    )

    no_coerce_none = EnumField(
        SmallPosIntEnum, coerce=False, null=True, db_default=None, blank=True
    )

    class Meta:
        ordering = ("id",)
