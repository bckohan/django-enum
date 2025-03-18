from django.db import models
from enum import Enum
from django_enum import EnumField
from pathlib import Path


class PathValueExample(models.Model):

    class PathEnum(Enum):

        USR = Path('/usr')
        USR_LOCAL = Path('/usr/local')
        USR_LOCAL_BIN = Path('/usr/local/bin')

    path = EnumField(PathEnum, primitive=str)
