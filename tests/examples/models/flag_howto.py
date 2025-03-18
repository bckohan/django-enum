# flake8: noqa
from enum import IntFlag
from django_enum import EnumField
from django.db import models


class Group(models.Model):

    class Permissions(IntFlag):

        # fmt: off
        READ    = 1 << 0
        WRITE   = 1 << 1
        EXECUTE = 1 << 2

        # IntFlags can have composite values!
        RWX     = READ | WRITE | EXECUTE
        # fmt: on

    permissions = EnumField(Permissions)
