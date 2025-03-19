# flake8: noqa
from django.db import models
from enum import IntFlag
from django_enum import EnumField


class Permissions(IntFlag):

    # fmt: off
    READ    = 1<<0
    WRITE   = 1<<1
    EXECUTE = 1<<2
    # fmt: on


class FlagExample(models.Model):

    permissions = EnumField(Permissions, null=True, blank=True)
