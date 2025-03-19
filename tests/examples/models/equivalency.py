from django.db import models
from django_enum import EnumField


class EquivalencyExample(models.Model):

    class TextEnum(models.TextChoices):

        VALUE0 = 'V0', 'Value 0'
        VALUE1 = 'V1', 'Value 1'
        VALUE2 = 'V2', 'Value 2'

    txt_enum = EnumField(TextEnum, null=True, blank=True, default=None)

    txt_choices = models.CharField(
        max_length=2,
        choices=TextEnum.choices,
        null=True,
        blank=True,
        default=None
    )
