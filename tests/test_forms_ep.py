import pytest

pytest.importorskip("enum_properties")
from tests.test_forms import FormTests, TestFormField
from tests.enum_prop.models import EnumTester, BitFieldModel
from tests.enum_prop.forms import EnumTesterForm
from tests.examples.models import FlagExample
from django_enum.forms import EnumFlagField, FlagSelectMultiple
from django.forms import ModelForm


class EnumPropertiesFormTests(FormTests):
    MODEL_CLASS = EnumTester


class TestFormFieldSymmetric(TestFormField):
    MODEL_CLASS = EnumTester
    FORM_CLASS = EnumTesterForm
    form_type = None

    @property
    def model_params(self):
        return {
            "small_pos_int": 0,
            "small_int": self.SmallIntEnum.VAL2,
            "pos_int": "Value 2147483647",
            "int": "VALn1",
            "big_pos_int": 2,
            "big_int": self.BigPosIntEnum.VAL2,
            "constant": "π",
            "text": "none",
            "extern": "three",
            "dj_int_enum": 2,
            "dj_text_enum": "B",
            "non_strict_int": 1,
            "non_strict_text": "arbitrary",
            "no_coerce": "Value 1",
        }

    def test_flag_choices_admin_form(self):
        from django.contrib import admin

        admin_class = admin.site._registry.get(BitFieldModel)
        self.assertIsInstance(
            admin_class.get_form(None).base_fields.get("bit_field_small"), EnumFlagField
        )

    def test_flag_choices_model_form(self):
        from tests.examples.models.flag import Permissions
        from tests.enum_prop.enums import GNSSConstellation

        class FlagChoicesModelForm(ModelForm):
            class Meta(EnumTesterForm.Meta):
                model = BitFieldModel

        form = FlagChoicesModelForm(
            data={"bit_field_small": [GNSSConstellation.GPS, GNSSConstellation.GLONASS]}
        )

        form.full_clean()
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["bit_field_small"],
            GNSSConstellation.GPS | GNSSConstellation.GLONASS,
        )
        self.assertIsInstance(form.base_fields["bit_field_small"], EnumFlagField)

    def test_extern_flag_admin_form(self):
        from django.contrib import admin

        admin_class = admin.site._registry.get(FlagExample)
        self.assertIsInstance(
            admin_class.get_form(None).base_fields.get("permissions"), EnumFlagField
        )

    def test_extern_flag_model_form(self):
        from tests.examples.models.flag import Permissions

        class FlagModelForm(ModelForm):
            class Meta(EnumTesterForm.Meta):
                model = FlagExample

        form = FlagModelForm(
            data={"permissions": [Permissions.READ, Permissions.WRITE]}
        )

        form.full_clean()
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["permissions"], Permissions.READ | Permissions.WRITE
        )
        self.assertIsInstance(form.base_fields["permissions"], EnumFlagField)

    def test_flag_select_multiple_format(self):
        from tests.examples.models.flag import Permissions

        widget = FlagSelectMultiple()  # no enum
        self.assertEqual(
            widget.format_value(Permissions.READ | Permissions.WRITE),
            [str(Permissions.READ.value), str(Permissions.WRITE.value)],
        )
        self.assertEqual(
            widget.format_value(Permissions.READ | Permissions.EXECUTE),
            [str(Permissions.READ.value), str(Permissions.EXECUTE.value)],
        )
        self.assertEqual(
            widget.format_value(Permissions.EXECUTE | Permissions.WRITE),
            [str(Permissions.WRITE.value), str(Permissions.EXECUTE.value)],
        )

        widget = FlagSelectMultiple(enum=Permissions)  # no enum
        self.assertEqual(
            widget.format_value(Permissions.READ | Permissions.WRITE),
            [str(Permissions.READ.value), str(Permissions.WRITE.value)],
        )
        self.assertEqual(
            widget.format_value(Permissions.READ | Permissions.EXECUTE),
            [str(Permissions.READ.value), str(Permissions.EXECUTE.value)],
        )
        self.assertEqual(
            widget.format_value(Permissions.EXECUTE | Permissions.WRITE),
            [str(Permissions.WRITE.value), str(Permissions.EXECUTE.value)],
        )

        # check pass through
        self.assertEqual(
            widget.format_value(
                [str(Permissions.WRITE.value), str(Permissions.EXECUTE.value)]
            ),
            [str(Permissions.WRITE.value), str(Permissions.EXECUTE.value)],
        )


FormTests = None
TestFormField = None
