from django.db import models
from django_enum import EnumField, TextChoices
from enum_properties import s


class MigrationTester(models.Model):

    # remove enumeration

    # no change
    class Color(TextChoices, s('rgb'), s('hex', case_fold=True)):
        # name   value   label       rgb       hex
        RD = 'R', 'Red', (1, 0, 0), 'ff0000'
        GR = 'G', 'Green', (0, 1, 0), '00ff00'
        BL = 'B', 'Blue', (0, 0, 1), '0000ff'

    color = EnumField(Color)
