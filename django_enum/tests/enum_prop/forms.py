from django.forms import ModelForm
from django_enum import EnumChoiceField
from django_enum.tests.enum_prop.enums import (
    SmallPosIntEnum,
    SmallIntEnum,
    PosIntEnum,
    IntEnum,
    BigIntEnum,
    BigPosIntEnum,
    Constants,
    TextEnum,
    DJIntEnum,
    DJTextEnum
)
from django_enum.tests.enum_prop.models import EnumTester


class EnumTesterForm(ModelForm):
    small_pos_int = EnumChoiceField(SmallPosIntEnum)
    small_int = EnumChoiceField(SmallIntEnum)
    pos_int = EnumChoiceField(PosIntEnum)
    int = EnumChoiceField(IntEnum)
    big_pos_int = EnumChoiceField(BigPosIntEnum)
    big_int = EnumChoiceField(BigIntEnum)
    constant = EnumChoiceField(Constants)
    text = EnumChoiceField(TextEnum)
    dj_int_enum = EnumChoiceField(DJIntEnum)
    dj_text_enum = EnumChoiceField(DJTextEnum)
    non_strict_int = EnumChoiceField(SmallPosIntEnum)

    class Meta:
        model = EnumTester
        fields = '__all__'
