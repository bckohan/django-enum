from django.db import models
from django_enum import TextChoices, EnumField
from enum_properties import s


class MigrationTester(models.Model):
    # unchanged
    class IntEnum(models.IntegerChoices):
        ONE = 1, 'One'
        TWO = 2, 'Two',
        THREE = 3, 'Three'

    # change enumeration names
    class Color(TextChoices, s('rgb'), s('hex', case_fold=True)):
        # name   value   label       rgb       hex
        RD = 'R', 'Red', (1, 0, 0), 'ff0000'
        GR = 'G', 'Green', (0, 1, 0), '00ff00'
        BL = 'B', 'Blue', (0, 0, 1), '0000ff'

    int_enum = EnumField(IntEnum)
    color = EnumField(Color)


