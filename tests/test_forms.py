from django.test import TestCase
from tests.utils import EnumTypeMixin
from tests.djenum.models import EnumTester
from tests.djenum.forms import EnumTesterForm
from django.forms import Form, ModelForm
from django_enum.forms import EnumChoiceField
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
            self.assertFalse(form.is_valid())
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
