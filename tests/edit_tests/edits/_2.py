import typing as t
from typing_extensions import Annotated

from django.db import models
from enum_properties import Symmetric

from django_enum import EnumField
from django_enum.choices import TextChoices


class MigrationTester(models.Model):
    # alter values (incr by 1)
    class IntEnum(models.IntegerChoices):
        ONE = 1, "One"
        TWO = (
            2,
            "Two",
        )
        THREE = 3, "Three"

    # unchanged
    class Color(TextChoices):
        rgb: Annotated[t.Tuple[int, int, int], Symmetric()]
        hex: Annotated[str, Symmetric(case_fold=True)]

        RED = "R", "Red", (1, 0, 0), "ff0000"
        GREEN = "G", "Green", (0, 1, 0), "00ff00"
        BLUE = "B", "Blue", (0, 0, 1), "0000ff"
        BLACK = "K", "Black", (0, 0, 0), "000000"

    int_enum = EnumField(IntEnum)
    color = EnumField(Color)
