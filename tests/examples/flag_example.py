from .models import FlagExample
from .models.flag import Permissions


instance = FlagExample.objects.create(
    permissions=Permissions.READ | Permissions.WRITE | Permissions.EXECUTE
)

# get all models with at least RW:
assert instance in FlagExample.objects.filter(
    permissions__has_all=Permissions.READ | Permissions.WRITE
)
