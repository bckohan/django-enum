from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms import ModelForm

from django_enum import EnumChoiceField
from django_enum.utils import choices
from tests.dataclass.enums import SmallPosIntEnum, TextEnum
from tests.dataclass.models import EnumTester


class EnumTesterForm(ModelForm):
    no_coerce = EnumChoiceField(
        SmallPosIntEnum,
        initial=None,
        choices=BLANK_CHOICE_DASH + choices(SmallPosIntEnum),
    )

    class Meta:
        model = EnumTester
        fields = "__all__"
