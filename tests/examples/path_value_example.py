from .models.path_value import PathValueExample
from django.db import models

obj = PathValueExample.objects.create(
    path=PathValueExample.PathEnum.USR_LOCAL_BIN,
)

assert isinstance(obj._meta.get_field("path"), models.CharField)
assert obj.path is PathValueExample.PathEnum.USR_LOCAL_BIN
