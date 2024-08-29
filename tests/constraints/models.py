from django.db import models

from django_enum import EnumField
from tests.constraints.enums import IntFlagEnum


class FlagConstraintTestModel(models.Model):
    flag_field = EnumField(IntFlagEnum, null=True, default=None, blank=True)

    flag_field_non_strict = EnumField(
        IntFlagEnum, null=True, default=None, blank=True, strict=False
    )
