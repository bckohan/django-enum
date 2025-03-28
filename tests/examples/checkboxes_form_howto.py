from .models.flag_howto import Group
from django.forms import Form
from django_enum.forms import EnumFlagField, FlagCheckbox, NonStrictFlagCheckbox
from django_enum import utils


class PermissionsExampleForm(Form):

    permissions = EnumFlagField(Group.Permissions, widget=FlagCheckbox)

    # form fields can be non-strict just like model fields.
    # for this field we add an additional flag for delete and
    # set the field to be non-strict
    permissions_ext = EnumFlagField(
        Group.Permissions,
        strict=False,
        choices=[
            *utils.choices(Group.Permissions),
            (1 << 3, "DELETE")
        ],
        widget=NonStrictFlagCheckbox
    )


form = PermissionsExampleForm(
    initial={
        "permissions": Group.Permissions.READ | Group.Permissions.EXECUTE,
        "permissions_ext": Group.Permissions.READ | Group.Permissions.WRITE | (1 << 3)
    }
)
