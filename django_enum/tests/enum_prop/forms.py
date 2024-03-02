try:

    from django.db.models import BLANK_CHOICE_DASH
    from django.forms import ModelForm

    from django_enum import EnumChoiceField
    from django_enum.tests.enum_prop.enums import SmallPosIntEnum, TextEnum
    from django_enum.tests.enum_prop.models import EnumTester

    class EnumTesterForm(ModelForm):
        no_coerce = EnumChoiceField(
            SmallPosIntEnum,
            initial=None,
            choices=BLANK_CHOICE_DASH + SmallPosIntEnum.choices,
        )

        class Meta:
            model = EnumTester
            fields = "__all__"

except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass
