from .models.flag_howto import Group
from django.forms import Form
from django_enum.forms import EnumFlagField
from django_enum import utils


class PermissionsExampleForm(Form):

    permissions = EnumFlagField(Group.Permissions)

    permissions_ext = EnumFlagField(
        Group.Permissions,
        choices=[
            ((Group.Permissions.READ | Group.Permissions.WRITE).value, 'RW')
        ] + utils.choices(Group.Permissions)
    )


form = PermissionsExampleForm(
    initial={
        "permissions": Group.Permissions.READ | Group.Permissions.EXECUTE,
        "permissions_ext": Group.Permissions.READ | Group.Permissions.WRITE
    }
)
