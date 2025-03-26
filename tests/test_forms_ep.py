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
        from django.forms.models import fields_for_model
        from django_enum.forms import EnumChoiceField, EnumFlagField
        from tests.examples.models.flag import Permissions
        from tests.enum_prop.enums import (
            GNSSConstellation,
            LargeBitField,
            LargeNegativeField,
        )

        class FlagChoicesModelForm(ModelForm):
            class Meta:
                fields = "__all__"
                model = BitFieldModel

        fields = fields_for_model(BitFieldModel)

        self.assertEqual(len(fields), 5)

        expected_types = {
            "bit_field_small": EnumFlagField,
            "bit_field_large": EnumFlagField,
            "bit_field_large_empty_default": EnumFlagField,
            "large_neg": EnumChoiceField,
            "no_default": EnumFlagField,
        }

        for field, inst in fields.items():
            self.assertIsInstance(inst, expected_types[field])

        form = FlagChoicesModelForm(
            data={
                "bit_field_small": [
                    GNSSConstellation.GPS.value,
                    GNSSConstellation.GLONASS,
                ],
                "large_neg": LargeNegativeField.NEG_ONE.value,
                "no_default": LargeBitField.TWO,
            }
        )

        form.full_clean()
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["bit_field_small"],
            GNSSConstellation.GPS | GNSSConstellation.GLONASS,
        )
        self.assertIsInstance(form.cleaned_data["bit_field_small"], GNSSConstellation)
        self.assertEqual(
            form.cleaned_data["large_neg"],
            LargeNegativeField.NEG_ONE,
        )
        self.assertIsInstance(form.cleaned_data["large_neg"], LargeNegativeField)
        self.assertEqual(form.cleaned_data["no_default"], LargeBitField.TWO)
        self.assertIsInstance(form.cleaned_data["no_default"], LargeBitField)
        self.assertEqual(form.cleaned_data["bit_field_large"], None)
        self.assertEqual(
            form.cleaned_data["bit_field_large_empty_default"], LargeBitField(0)
        )
        self.assertIsInstance(
            form.cleaned_data["bit_field_large_empty_default"], LargeBitField
        )
        self.assertIsInstance(form.base_fields["bit_field_small"], EnumFlagField)

        self.assertEqual(
            form.base_fields["bit_field_small"].empty_value, GNSSConstellation(0)
        )
        self.assertEqual(form.base_fields["bit_field_large"].empty_value, None)
        self.assertEqual(
            form.base_fields["bit_field_large_empty_default"].empty_value,
            LargeBitField(0),
        )
        self.assertEqual(form.base_fields["large_neg"].empty_value, None)
        self.assertEqual(form.base_fields["no_default"].empty_value, LargeBitField(0))

    def test_extern_flag_admin_form(self):
        from django.contrib import admin

        admin_class = admin.site._registry.get(FlagExample)
        self.assertIsInstance(
            admin_class.get_form(None).base_fields.get("permissions"), EnumFlagField
        )

    def test_extern_flag_model_form(self):
        from tests.examples.models.flag import Permissions

        class FlagModelForm(ModelForm):
            class Meta:
                fields = "__all__"
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

        widget = FlagSelectMultiple(enum=Permissions)
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
