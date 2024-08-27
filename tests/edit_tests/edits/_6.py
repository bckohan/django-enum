from django.db import models
from enum_properties import s

from django_enum import EnumField, TextChoices


class MigrationTester(models.Model):
    # unchanged
    class IntEnum(models.IntegerChoices):
        ONE = 1, "One"
        TWO = (
            2,
            "Two",
        )
        THREE = 3, "Three"
        FOUR = 32768, "Four"  # force column size to increase

    # change enumeration names
    class Color(TextChoices, s("rgb"), s("hex", case_fold=True)):
        # name   value   label       rgb       hex
        RD = "R", "Red", (1, 0, 0), "ff0000"
        GR = "G", "Green", (0, 1, 0), "00ff00"
        BL = "B", "Blue", (0, 0, 1), "0000ff"

    # should remove the check constraint
    int_enum = EnumField(IntEnum, strict=False)
    color = EnumField(Color)
