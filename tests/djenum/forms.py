from django.forms import ModelForm, Form
from django_enum.forms import EnumMultipleChoiceField
from tests.djenum.models import EnumTester
from tests.djenum.enums import (
    SmallPosIntEnum,
    SmallIntEnum,
    PosIntEnum,
    IntEnum,
    BigPosIntEnum,
    BigIntEnum,
    Constants,
    TextEnum,
    ExternEnum,
    DJIntEnum,
    DJTextEnum,
    DateEnum,
    DateTimeEnum,
    DecimalEnum,
    TimeEnum,
    DurationEnum,
)


class EnumTesterForm(ModelForm):
    class Meta:
        model = EnumTester
        fields = "__all__"


class EnumTesterMultipleChoiceForm(Form):
    small_pos_int = EnumMultipleChoiceField(SmallPosIntEnum)
    small_int = EnumMultipleChoiceField(SmallIntEnum)
    pos_int = EnumMultipleChoiceField(PosIntEnum)
    int = EnumMultipleChoiceField(IntEnum)
    big_pos_int = EnumMultipleChoiceField(BigPosIntEnum)
    big_int = EnumMultipleChoiceField(BigIntEnum)
    constant = EnumMultipleChoiceField(Constants)
    text = EnumMultipleChoiceField(TextEnum)
    extern = EnumMultipleChoiceField(ExternEnum)

    # Non-strict
    non_strict_int = EnumMultipleChoiceField(SmallPosIntEnum, strict=False)
    non_strict_text = EnumMultipleChoiceField(TextEnum, strict=False)
    no_coerce = EnumMultipleChoiceField(SmallPosIntEnum, strict=False)

    # eccentric enums
    date_enum = EnumMultipleChoiceField(DateEnum)
    datetime_enum = EnumMultipleChoiceField(DateTimeEnum)
    time_enum = EnumMultipleChoiceField(TimeEnum)
    duration_enum = EnumMultipleChoiceField(DurationEnum)
    decimal_enum = EnumMultipleChoiceField(DecimalEnum)
