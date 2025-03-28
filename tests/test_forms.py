from django.test import TestCase
import pytest
import django
from django.db import connection
from django.contrib import admin
from tests.utils import EnumTypeMixin
from tests.djenum.models import EnumTester, Bug53Tester, NullableStrEnum
from tests.djenum.forms import EnumTesterForm, EnumTesterMultipleChoiceForm
from django.forms import Form, ModelForm
from django_enum.forms import EnumChoiceField, EnumMultipleChoiceField
from django.core.exceptions import ValidationError
from datetime import date, datetime, timedelta, time
from decimal import Decimal


class FormTests(EnumTypeMixin, TestCase):
    """
    Some more explicit form tests that allow easier access to other internal workflows.
    """

    MODEL_CLASS = EnumTester

    @property
    def model_form_class(self):
        class EnumTesterForm(ModelForm):
            class Meta:
                model = self.MODEL_CLASS
                fields = "__all__"

        return EnumTesterForm

    @property
    def basic_form_class(self):
        from django.core.validators import MaxValueValidator, MinValueValidator

        class BasicForm(Form):
            small_pos_int = EnumChoiceField(self.SmallPosIntEnum)
            small_int = EnumChoiceField(self.SmallIntEnum)
            pos_int = EnumChoiceField(self.PosIntEnum)
            int = EnumChoiceField(self.IntEnum)
            big_pos_int = EnumChoiceField(self.BigPosIntEnum)
            big_int = EnumChoiceField(self.BigIntEnum)
            constant = EnumChoiceField(self.Constants)
            text = EnumChoiceField(self.TextEnum)
            extern = EnumChoiceField(self.ExternEnum)
            dj_int_enum = EnumChoiceField(self.DJIntEnum)
            dj_text_enum = EnumChoiceField(self.DJTextEnum)
            non_strict_int = EnumChoiceField(self.SmallPosIntEnum, strict=False)
            non_strict_text = EnumChoiceField(self.TextEnum, strict=False)
            no_coerce = EnumChoiceField(
                self.SmallPosIntEnum,
                validators=[MinValueValidator(0), MaxValueValidator(32767)],
            )

        return BasicForm

    @property
    def test_params(self):
        return {
            "small_pos_int": self.SmallPosIntEnum.VAL2,
            "small_int": self.SmallIntEnum.VALn1,
            "pos_int": self.PosIntEnum.VAL3,
            "int": self.IntEnum.VALn1,
            "big_pos_int": self.BigPosIntEnum.VAL3,
            "big_int": self.BigIntEnum.VAL2,
            "constant": self.Constants.GOLDEN_RATIO,
            "text": self.TextEnum.VALUE2,
            "extern": self.ExternEnum.TWO,
            "dj_int_enum": self.DJIntEnum.THREE,
            "dj_text_enum": self.DJTextEnum.A,
            "non_strict_int": "15",
            "non_strict_text": "arbitrary",
            "no_coerce": self.SmallPosIntEnum.VAL3,
        }

    @property
    def test_data_strings(self):
        return {
            **{key: str(value) for key, value in self.test_params.items()},
            "extern": str(self.ExternEnum.TWO.value),
        }

    @property
    def expected(self):
        return {
            **self.test_params,
            "non_strict_int": int(self.test_params["non_strict_int"]),
        }

    def test_modelform_binding(self):
        form = self.model_form_class(data=self.test_data_strings)

        form.full_clean()
        self.assertTrue(form.is_valid())

        for key, value in self.expected.items():
            self.assertEqual(form.cleaned_data[key], value)

        self.assertIsInstance(form.cleaned_data["no_coerce"], int)
        self.assertIsInstance(form.cleaned_data["non_strict_int"], int)

        obj = form.save()

        for key, value in self.expected.items():
            self.assertEqual(getattr(obj, key), value)

    def test_basicform_binding(self):
        form = self.basic_form_class(data=self.test_data_strings)
        form.full_clean()
        self.assertTrue(form.is_valid())

        for key, value in self.expected.items():
            self.assertEqual(form.cleaned_data[key], value)

        self.assertIsInstance(form.cleaned_data["no_coerce"], int)
        self.assertIsInstance(form.cleaned_data["non_strict_int"], int)


class NullBlankBehaviorTests(TestCase):
    def test_bug53_form(self):
        from tests.djenum.models import Bug53Tester

        class Bug53TesterForm(ModelForm):
            class Meta:
                fields = "__all__"
                model = Bug53Tester

        form = Bug53TesterForm()

        self.assertIsInstance(form.base_fields["char_blank_null_true"], EnumChoiceField)
        self.assertIsInstance(
            form.base_fields["char_blank_null_false"], EnumChoiceField
        )
        self.assertIsInstance(
            form.base_fields["char_blank_null_false_default"], EnumChoiceField
        )
        self.assertIsInstance(form.base_fields["int_blank_null_false"], EnumChoiceField)

        self.assertEqual(form.base_fields["char_blank_null_true"].empty_value, None)
        self.assertEqual(form.base_fields["char_blank_null_false"].empty_value, "")
        self.assertEqual(
            form.base_fields["char_blank_null_false_default"].empty_value, ""
        )
        self.assertEqual(form.base_fields["int_blank_null_false"].empty_value, "")
        self.assertEqual(form.base_fields["int_blank_null_true"].empty_value, None)

    def test_null_blank_tester_form(self):
        from tests.djenum.models import NullBlankFormTester
        from tests.djenum.enums import ExternEnum

        class NullBlankFormTesterForm(ModelForm):
            class Meta:
                fields = "__all__"
                model = NullBlankFormTester

        form = NullBlankFormTesterForm(
            data={
                "required": ExternEnum.TWO,
                "required_default": ExternEnum.ONE,
                "blank": None,
            }
        )

        # null=False, blank=false
        self.assertEqual(
            form.base_fields["required"].choices,
            [("", "---------"), (1, "ONE"), (2, "TWO"), (3, "THREE")],
        )
        # null=False, blank=false, default=TWO
        self.assertEqual(
            form.base_fields["required_default"].choices,
            [(1, "ONE"), (2, "TWO"), (3, "THREE")],
        )
        # null=False, blank=True
        self.assertEqual(
            form.base_fields["blank"].choices,
            [("", "---------"), (1, "ONE"), (2, "TWO"), (3, "THREE")],
        )
        # null=True, blank=True
        self.assertEqual(
            form.base_fields["blank_nullable"].choices,
            [("", "---------"), (1, "ONE"), (2, "TWO"), (3, "THREE")],
        )
        # null=True, blank=True, default=None
        self.assertEqual(
            form.base_fields["blank_nullable_default"].choices,
            [("", "---------"), (1, "ONE"), (2, "TWO"), (3, "THREE")],
        )

        with self.assertRaises(ValueError):
            # because blank will error out on save - this is correct behavior
            # because the form allows blank, but the field does not - this is an
            # issue with how the user specifies their field (null=False, blank=True)
            # with no blank value conversion
            form.full_clean()
            form.save()

        # the form is valid because the error happens on model save!
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["required"], ExternEnum.TWO)
        self.assertEqual(form.cleaned_data["required_default"], ExternEnum.ONE)
        self.assertIsInstance(form.base_fields["required"], EnumChoiceField)

    @pytest.mark.skipif(
        connection.vendor == "oracle",
        reason="Null/blank form behavior on oracle broken",
    )
    def test_nullable_blank_tester_form(self):
        from tests.djenum.models import NullableBlankFormTester
        from tests.djenum.enums import NullableExternEnum

        class NullableBlankFormTesterForm(ModelForm):
            class Meta:
                fields = "__all__"
                model = NullableBlankFormTester

        form = NullableBlankFormTesterForm(
            data={
                "required": NullableExternEnum.TWO,
                "required_default": NullableExternEnum.ONE,
            }
        )

        # null=False, blank=false
        self.assertEqual(
            form.base_fields["required"].choices,
            [(None, "NONE"), (1, "ONE"), (2, "TWO"), (3, "THREE")],
        )
        # null=False, blank=false, default=TWO
        self.assertEqual(
            form.base_fields["required_default"].choices,
            [(None, "NONE"), (1, "ONE"), (2, "TWO"), (3, "THREE")],
        )
        # null=False, blank=True
        self.assertEqual(
            form.base_fields["blank"].choices,
            [(None, "NONE"), (1, "ONE"), (2, "TWO"), (3, "THREE")],
        )
        # null=True, blank=True
        self.assertEqual(
            form.base_fields["blank_nullable"].choices,
            [(None, "NONE"), (1, "ONE"), (2, "TWO"), (3, "THREE")],
        )
        # null=True, blank=True, default=None
        self.assertEqual(
            form.base_fields["blank_nullable_default"].choices,
            [(None, "NONE"), (1, "ONE"), (2, "TWO"), (3, "THREE")],
        )

        form.full_clean()

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["required"], NullableExternEnum.TWO)
        self.assertEqual(form.cleaned_data["required_default"], NullableExternEnum.ONE)
        self.assertIsInstance(form.base_fields["required"], EnumChoiceField)

    @pytest.mark.skipif(
        connection.vendor == "oracle",
        reason="Null/blank form behavior on oracle broken",
    )
    def test_nullable_str_tester_form(self):
        from tests.djenum.models import NullableStrFormTester
        from tests.djenum.enums import NullableStrEnum

        class NullableStrEnumForm(ModelForm):
            class Meta:
                fields = "__all__"
                model = NullableStrFormTester

        form = NullableStrEnumForm(
            data={
                "required": NullableStrEnum.STR1,
                "required_default": NullableStrEnum.STR2,
            }
        )

        # null=False, blank=false
        self.assertEqual(
            form.base_fields["required"].choices,
            [(None, "NONE"), ("str1", "STR1"), ("str2", "STR2")],
        )
        # null=False, blank=false, default=TWO
        self.assertEqual(
            form.base_fields["required_default"].choices,
            [(None, "NONE"), ("str1", "STR1"), ("str2", "STR2")],
        )
        # null=False, blank=True
        self.assertEqual(
            form.base_fields["blank"].choices,
            [(None, "NONE"), ("str1", "STR1"), ("str2", "STR2")],
        )
        # null=True, blank=True
        self.assertEqual(
            form.base_fields["blank_nullable"].choices,
            [(None, "NONE"), ("str1", "STR1"), ("str2", "STR2")],
        )
        # null=True, blank=True, default=None
        self.assertEqual(
            form.base_fields["blank_nullable_default"].choices,
            [(None, "NONE"), ("str1", "STR1"), ("str2", "STR2")],
        )

        form.full_clean()

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["required"], NullableStrEnum.STR1)
        self.assertEqual(form.cleaned_data["required_default"], NullableStrEnum.STR2)
        self.assertIsInstance(form.base_fields["required"], EnumChoiceField)


class TestFormField(EnumTypeMixin, TestCase):
    MODEL_CLASS = EnumTester
    FORM_CLASS = EnumTesterForm
    form_type = None

    @property
    def model_params(self):
        return {
            "small_pos_int": 0,
            "small_int": self.SmallIntEnum.VAL2,
            "pos_int": 2147483647,
            "int": self.IntEnum.VALn1,
            "big_pos_int": 2,
            "big_int": self.BigIntEnum.VAL0,
            "constant": 2.71828,
            "text": self.TextEnum.VALUE3,
            "extern": self.ExternEnum.THREE,
            "date_enum": self.DateEnum.BRIAN,
            "datetime_enum": self.DateTimeEnum.ST_HELENS,
            "duration_enum": self.DurationEnum.FORTNIGHT,
            "time_enum": self.TimeEnum.COB,
            "decimal_enum": self.DecimalEnum.ONE,
            "dj_int_enum": 2,
            "dj_text_enum": self.DJTextEnum.B,
            "non_strict_int": self.SmallPosIntEnum.VAL2,
            "non_strict_text": "arbitrary",
            "no_coerce": self.SmallPosIntEnum.VAL1,
        }

    @property
    def bad_values(self):
        return {
            "small_pos_int": 4.1,
            "small_int": "Value 12",
            "pos_int": 5.3,
            "int": 10,
            "big_pos_int": "-12",
            "big_int": "-12",
            "constant": 2.7,
            "text": "143 emma",
            "date_enum": "20159-01-01",
            "datetime_enum": "AAAA-01-01 00:00:00",
            "duration_enum": "1 elephant",
            "time_enum": "2.a",
            "decimal_enum": "alpha",
            "extern": 6,
            "dj_int_enum": "",
            "dj_text_enum": "D",
            "non_strict_int": "Not an int",
            "non_strict_text": "A" * 13,
            "no_coerce": "Value 0",
        }

    from json import encoder

    def verify_field(self, form, field, value):
        # this doesnt work with coerce=False fields
        if self.MODEL_CLASS._meta.get_field(field).coerce:
            self.assertIsInstance(form[field].value(), self.enum_primitive(field))
        #######
        if self.MODEL_CLASS._meta.get_field(field).strict:
            self.assertEqual(form[field].value(), self.enum_type(field)(value).value)
            if self.MODEL_CLASS._meta.get_field(field).coerce:
                self.assertIsInstance(
                    form[field].field.to_python(form[field].value()),
                    self.enum_type(field),
                )
        else:
            self.assertEqual(form[field].value(), value)

    def test_initial(self):
        form = self.FORM_CLASS(initial=self.model_params)
        for field, value in self.model_params.items():
            self.verify_field(form, field, value)

    def test_instance(self):
        instance = self.MODEL_CLASS.objects.create(**self.model_params)
        form = self.FORM_CLASS(instance=instance)
        for field, value in self.model_params.items():
            self.verify_field(form, field, value)
        instance.delete()

    def test_data(self):
        form = self.FORM_CLASS(data=self.model_params)
        form.full_clean()
        self.assertTrue(form.is_valid())
        for field, value in self.model_params.items():
            self.verify_field(form, field, value)

    def test_error(self):
        for field, bad_value in self.bad_values.items():
            form = self.FORM_CLASS(data={**self.model_params, field: bad_value})
            form.full_clean()
            self.assertFalse(form.is_valid(), f"{field}={bad_value}")
            self.assertTrue(field in form.errors)

        form = self.FORM_CLASS(data=self.bad_values)
        form.full_clean()
        self.assertFalse(form.is_valid())
        for field in self.bad_values.keys():
            self.assertTrue(field in form.errors)

    def test_field_validation(self):
        for enum_field, bad_value in [
            (EnumChoiceField(self.SmallPosIntEnum), 4.1),
            (EnumChoiceField(self.SmallIntEnum), 123123123),
            (EnumChoiceField(self.PosIntEnum), -1),
            (EnumChoiceField(self.IntEnum), "63"),
            (EnumChoiceField(self.BigPosIntEnum), None),
            (EnumChoiceField(self.BigIntEnum), ""),
            (EnumChoiceField(self.Constants), "y"),
            (EnumChoiceField(self.TextEnum), 42),
            (EnumChoiceField(self.DateEnum), "20159-01-01"),
            (EnumChoiceField(self.DateTimeEnum), "AAAA-01-01 00:00:00"),
            (EnumChoiceField(self.DurationEnum), "1 elephant"),
            (EnumChoiceField(self.TimeEnum), "2.a"),
            (EnumChoiceField(self.DecimalEnum), "alpha"),
            (EnumChoiceField(self.ExternEnum), 0),
            (EnumChoiceField(self.DJIntEnum), "5.3"),
            (EnumChoiceField(self.DJTextEnum), 12),
            (EnumChoiceField(self.SmallPosIntEnum, strict=False), "not an int"),
        ]:
            self.assertRaises(ValidationError, enum_field.validate, bad_value)

        for enum_field, bad_value in [
            (EnumChoiceField(self.SmallPosIntEnum, strict=False), 4),
            (EnumChoiceField(self.SmallIntEnum, strict=False), 123123123),
            (EnumChoiceField(self.PosIntEnum, strict=False), -1),
            (EnumChoiceField(self.IntEnum, strict=False), "63"),
            (EnumChoiceField(self.BigPosIntEnum, strict=False), 18),
            (EnumChoiceField(self.BigIntEnum, strict=False), "-8"),
            (EnumChoiceField(self.Constants, strict=False), "1.976"),
            (EnumChoiceField(self.TextEnum, strict=False), 42),
            (EnumChoiceField(self.ExternEnum, strict=False), 0),
            (EnumChoiceField(self.DJIntEnum, strict=False), "5"),
            (EnumChoiceField(self.DJTextEnum, strict=False), 12),
            (EnumChoiceField(self.SmallPosIntEnum, strict=False), "12"),
            (
                EnumChoiceField(self.DateEnum, strict=False),
                date(year=2015, month=1, day=1),
            ),
            (
                EnumChoiceField(self.DateTimeEnum, strict=False),
                datetime(year=2014, month=1, day=1, hour=0, minute=0, second=0),
            ),
            (EnumChoiceField(self.DurationEnum, strict=False), timedelta(seconds=15)),
            (
                EnumChoiceField(self.TimeEnum, strict=False),
                time(hour=2, minute=0, second=0),
            ),
            (EnumChoiceField(self.DecimalEnum, strict=False), Decimal("0.5")),
        ]:
            try:
                enum_field.clean(bad_value)
            except ValidationError:  # pragma: no cover
                self.fail(
                    f"non-strict choice field for {enum_field.enum} raised ValidationError on {bad_value} during clean"
                )

    def test_non_strict_field(self):
        form = self.FORM_CLASS(data={**self.model_params, "non_strict_int": 200})
        form.full_clean()
        self.assertTrue(form.is_valid())
        self.assertIsInstance(
            form["non_strict_int"].value(), self.enum_primitive("non_strict_int")
        )
        self.assertEqual(form["non_strict_int"].value(), 200)
        self.assertIsInstance(
            form["non_strict_int"].field.to_python(form["non_strict_int"].value()),
            self.enum_primitive("non_strict_int"),
        )


class TestEnumMultipleChoiceFormField(EnumTypeMixin, TestCase):
    MODEL_CLASS = EnumTester
    FORM_CLASS = EnumTesterMultipleChoiceForm
    form_type = None

    @property
    def model_params(self):
        return {
            "small_pos_int": [0],
            "small_int": [self.SmallIntEnum.VAL2, self.SmallIntEnum.VALn1],
            "pos_int": [2147483647, self.PosIntEnum.VAL3],
            "int": [self.IntEnum.VALn1],
            "big_pos_int": [2, self.BigPosIntEnum.VAL3],
            "big_int": [self.BigIntEnum.VAL0],
            "constant": [2.71828, self.Constants.GOLDEN_RATIO],
            "text": [self.TextEnum.VALUE3, self.TextEnum.VALUE2],
            "extern": [self.ExternEnum.THREE],
            "date_enum": [self.DateEnum.BRIAN, date(1989, 7, 27)],
            "datetime_enum": [self.DateTimeEnum.ST_HELENS, self.DateTimeEnum.ST_HELENS],
            "duration_enum": [self.DurationEnum.FORTNIGHT],
            "time_enum": [self.TimeEnum.COB, self.TimeEnum.LUNCH],
            "decimal_enum": [self.DecimalEnum.ONE],
            "non_strict_int": [self.SmallPosIntEnum.VAL2],
            "non_strict_text": ["arbitrary", "A" * 13],
            "no_coerce": [self.SmallPosIntEnum.VAL1],
        }

    @property
    def bad_values(self):
        return {
            "small_pos_int": [4.1],
            "small_int": ["Value 12"],
            "pos_int": [5.3],
            "int": [10],
            "big_pos_int": ["-12"],
            "big_int": ["-12"],
            "constant": [2.7],
            "text": ["143 emma"],
            "date_enum": ["20159-01-01"],
            "datetime_enum": ["AAAA-01-01 00:00:00"],
            "duration_enum": ["1 elephant"],
            "time_enum": ["2.a"],
            "decimal_enum": ["alpha"],
            "extern": [6],
            "non_strict_int": ["Not an int"],
            "non_strict_text": [],
            "no_coerce": ["Value 0"],
        }

    from json import encoder

    def verify_field(self, form, field, values):
        # this doesnt work with coerce=False fields
        for idx, value in enumerate(values):
            if self.MODEL_CLASS._meta.get_field(field).strict:
                self.assertEqual(
                    form[field].value()[idx], self.enum_type(field)(value).value
                )
                self.assertIsInstance(
                    form[field].field.to_python(form[field].value())[idx],
                    self.enum_type(field),
                )

    def test_initial(self):
        form = self.FORM_CLASS(initial=self.model_params)
        for field, values in self.model_params.items():
            self.verify_field(form, field, values)

    def test_data(self):
        form = self.FORM_CLASS(data=self.model_params)
        form.full_clean()
        self.assertTrue(form.is_valid())
        for field, values in self.model_params.items():
            self.verify_field(form, field, values)

    def test_error(self):
        for field, bad_value in self.bad_values.items():
            form = self.FORM_CLASS(data={**self.model_params, field: bad_value})
            form.full_clean()
            self.assertFalse(form.is_valid(), f"{field}={bad_value}: {form.errors}")
            self.assertTrue(field in form.errors)

        form = self.FORM_CLASS(data=self.bad_values)
        form.full_clean()
        self.assertFalse(form.is_valid())
        for field in self.bad_values.keys():
            self.assertTrue(field in form.errors)

    def test_field_validation(self):
        for enum_field, bad_value in [
            (EnumMultipleChoiceField(self.SmallPosIntEnum), 4.1),
            (EnumMultipleChoiceField(self.SmallIntEnum), 123123123),
            (EnumMultipleChoiceField(self.PosIntEnum), -1),
            (EnumMultipleChoiceField(self.IntEnum), "63"),
            (EnumMultipleChoiceField(self.BigPosIntEnum), None),
            (EnumMultipleChoiceField(self.BigIntEnum), ""),
            (EnumMultipleChoiceField(self.Constants), "y"),
            (EnumMultipleChoiceField(self.TextEnum), 42),
            (EnumMultipleChoiceField(self.DateEnum), "20159-01-01"),
            (EnumMultipleChoiceField(self.DateTimeEnum), "AAAA-01-01 00:00:00"),
            (EnumMultipleChoiceField(self.DurationEnum), "1 elephant"),
            (EnumMultipleChoiceField(self.TimeEnum), "2.a"),
            (EnumMultipleChoiceField(self.DecimalEnum), "alpha"),
            (EnumMultipleChoiceField(self.ExternEnum), 0),
            (EnumMultipleChoiceField(self.DJIntEnum), "5.3"),
            (EnumMultipleChoiceField(self.DJTextEnum), 12),
            (EnumMultipleChoiceField(self.SmallPosIntEnum, strict=False), "not an int"),
        ]:
            self.assertRaises(ValidationError, enum_field.validate, [bad_value])

        for enum_field, bad_value in [
            (EnumMultipleChoiceField(self.SmallPosIntEnum, strict=False), 4),
            (EnumMultipleChoiceField(self.SmallIntEnum, strict=False), 123123123),
            (EnumMultipleChoiceField(self.PosIntEnum, strict=False), -1),
            (EnumMultipleChoiceField(self.IntEnum, strict=False), "63"),
            (EnumMultipleChoiceField(self.BigPosIntEnum, strict=False), 18),
            (EnumMultipleChoiceField(self.BigIntEnum, strict=False), "-8"),
            (EnumMultipleChoiceField(self.Constants, strict=False), "1.976"),
            (EnumMultipleChoiceField(self.TextEnum, strict=False), 42),
            (EnumMultipleChoiceField(self.ExternEnum, strict=False), 0),
            (EnumMultipleChoiceField(self.DJIntEnum, strict=False), "5"),
            (EnumMultipleChoiceField(self.DJTextEnum, strict=False), 12),
            (EnumMultipleChoiceField(self.SmallPosIntEnum, strict=False), "12"),
            (
                EnumMultipleChoiceField(self.DateEnum, strict=False),
                date(year=2015, month=1, day=1),
            ),
            (
                EnumMultipleChoiceField(self.DateTimeEnum, strict=False),
                datetime(year=2014, month=1, day=1, hour=0, minute=0, second=0),
            ),
            (
                EnumMultipleChoiceField(self.DurationEnum, strict=False),
                timedelta(seconds=15),
            ),
            (
                EnumMultipleChoiceField(self.TimeEnum, strict=False),
                time(hour=2, minute=0, second=0),
            ),
            (EnumMultipleChoiceField(self.DecimalEnum, strict=False), Decimal("0.5")),
        ]:
            try:
                enum_field.clean([bad_value])
            except ValidationError:  # pragma: no cover
                self.fail(
                    f"non-strict choice field for {enum_field.enum} "
                    f"raised ValidationError on {bad_value} during clean"
                )

    def test_non_strict_field(self):
        form = self.FORM_CLASS(data={**self.model_params, "non_strict_int": [200, 203]})
        form.full_clean()
        self.assertTrue(form.is_valid())
        for idx in range(0, 2):
            self.assertIsInstance(
                form["non_strict_int"].value()[idx],
                self.enum_primitive("non_strict_int"),
            )
            self.assertIsInstance(
                form["non_strict_int"].field.to_python(form["non_strict_int"].value())[
                    idx
                ],
                self.enum_primitive("non_strict_int"),
            )
        self.assertEqual(form["non_strict_int"].value(), [200, 203])

    def test_has_changed(self):
        {
            "small_pos_int": [0],
            "small_int": [self.SmallIntEnum.VAL2, self.SmallIntEnum.VALn1],
            "pos_int": [2147483647, self.PosIntEnum.VAL3],
            "int": [self.IntEnum.VALn1],
            "big_pos_int": [2, self.BigPosIntEnum.VAL3],
            "big_int": [self.BigIntEnum.VAL0],
            "constant": [2.71828, self.Constants.GOLDEN_RATIO],
            "text": [self.TextEnum.VALUE3, self.TextEnum.VALUE2],
            "extern": [self.ExternEnum.THREE],
            "date_enum": [self.DateEnum.BRIAN, date(1989, 7, 27)],
            "datetime_enum": [self.DateTimeEnum.ST_HELENS, self.DateTimeEnum.ST_HELENS],
            "duration_enum": [self.DurationEnum.FORTNIGHT],
            "time_enum": [self.TimeEnum.COB, self.TimeEnum.LUNCH],
            "decimal_enum": [self.DecimalEnum.ONE],
            "non_strict_int": [self.SmallPosIntEnum.VAL2],
            "non_strict_text": ["arbitrary", "A" * 13],
            "no_coerce": [self.SmallPosIntEnum.VAL1],
        }
        form = self.FORM_CLASS(
            data={"small_pos_int": [self.SmallPosIntEnum.VAL1]},
            initial={"small_pos_int": [0]},
        )
        self.assertFalse(form.has_changed())

        form = self.FORM_CLASS(
            data={"small_pos_int": [self.SmallPosIntEnum.VAL2]},
            initial={"small_pos_int": [0]},
        )
        self.assertTrue(form.has_changed())

        form = self.FORM_CLASS(
            data={"small_pos_int": [self.SmallPosIntEnum.VAL1.value]},
            initial={"small_pos_int": [self.SmallPosIntEnum.VAL1]},
        )
        self.assertFalse(form.has_changed())

        form = self.FORM_CLASS(
            data={"small_pos_int": [self.SmallPosIntEnum.VAL2.value]},
            initial={"small_pos_int": [self.SmallPosIntEnum.VAL1]},
        )
        self.assertTrue(form.has_changed())

        form = self.FORM_CLASS(
            data={"small_pos_int": [str(self.SmallPosIntEnum.VAL1.value)]},
            initial={"small_pos_int": [self.SmallPosIntEnum.VAL1]},
        )
        self.assertFalse(form.has_changed())

        form = self.FORM_CLASS(
            data={"small_pos_int": [str(self.SmallPosIntEnum.VAL2.value)]},
            initial={"small_pos_int": [self.SmallPosIntEnum.VAL1]},
        )
        self.assertTrue(form.has_changed())


def test_flag_mixin_value_passthrough():
    """
    This test is mostly for coverage - we may need to alter this behavior later,
    it catches the passthrough case for unrecognized Flag field values during rendering.
    """
    from django_enum.forms import FlagMixin

    assert FlagMixin().format_value((1, 2, 3)) == (1, 2, 3)
