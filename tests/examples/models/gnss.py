# flake8: noqa
from django.db import models
from enum import IntFlag
from django_enum import EnumField


class Constellation(IntFlag):

    # fmt: off
    GPS     = 1 << 0  # 1
    GLONASS = 1 << 1  # 2
    GALILEO = 1 << 2  # 4
    BEIDOU  = 1 << 3  # 8
    QZSS    = 1 << 4  # 16
    IRNSS   = 1 << 5  # 32
    # fmt: on


class GNSSReceiver(models.Model):

    constellations = EnumField(Constellation, db_index=True)
