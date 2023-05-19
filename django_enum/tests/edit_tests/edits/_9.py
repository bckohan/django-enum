from django.db import models
from django_enum import EnumField, TextChoices
from enum_properties import s


class MigrationTester(models.Model):

    class IntEnum(models.TextChoices):
        A = 'A', 'One'
        B = 'B', 'Two',
        C = 'C', 'Three'

    class Color(TextChoices, s('rgb'), s('hex', case_fold=True)):
        RED = 'R', 'Red', (1, 0, 0), 'ff0000'
        GREEN = 'G', 'Green', (0, 1, 0), '00ff00'

        # change meaning of default indirectly
        BLUE = 'B', 'Blue', (0, 0, 1), '000000'
        BLACK = 'K', 'Black', (0, 0, 0), '0000ff'

    int_enum = EnumField(IntEnum, null=True, default=None)

    # default value unchanged
    color = EnumField(Color, default='000000')
