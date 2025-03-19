from django.db import models
from django_enum import EnumField


class StrictExample(models.Model):

    class EnumType(models.TextChoices):

        ONE = "1", "One"
        TWO = "2", "Two"

    non_strict = EnumField(
        EnumType,
        strict=False,
        # it might be necessary to override max_length also,
        # otherwise max_length will be 1
        max_length=10,
    )
