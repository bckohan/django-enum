from django.db import models
from enum_properties import s

from django_enum import EnumField, TextChoices


class MigrationTester(models.Model):
    class IntEnum(models.IntegerChoices):
        ONE = 0, "One"
        TWO = (
            1,
            "Two",
        )
        THREE = 2, "Three"

    class Color(TextChoices, s("rgb"), s("hex", case_fold=True)):
        RED = "R", "Red", (1, 0, 0), "ff0000"
        GREEN = "G", "Green", (0, 1, 0), "00ff00"
        BLUE = "B", "Blue", (0, 0, 1), "0000ff"
        BLACK = "K", "Black", (0, 0, 0), "000000"

    int_enum = EnumField(IntEnum)
    color = EnumField(Color)
