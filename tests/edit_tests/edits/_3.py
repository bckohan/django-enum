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

    # remove black
    class Color(TextChoices, s("rgb"), s("hex", case_fold=True)):
        # name   value   label       rgb       hex
        RED = "R", "Red", (1, 0, 0), "ff0000"
        GREEN = "G", "Green", (0, 1, 0), "00ff00"
        BLUE = "B", "Blue", (0, 0, 1), "0000ff"

    int_enum = EnumField(IntEnum)
    color = EnumField(Color)
