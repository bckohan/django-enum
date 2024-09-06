import pytest

pytest.importorskip("enum_properties")

from tests.test_choices import TestChoices as BaseTestChoices
from django_enum.choices import FlagChoices
from tests.enum_prop.models import EnumTester
from datetime import date, datetime, time, timedelta
from decimal import Decimal


class TestChoicesEnumProp(BaseTestChoices):
    MODEL_CLASS = EnumTester

    @property
    def create_params(self):
        return {
            "small_pos_int": self.SmallPosIntEnum.VAL2,
            "small_int": "Value -32768",
            "pos_int": 2147483647,
            "int": -2147483648,
            "big_pos_int": "Value 2147483648",
            "big_int": "VAL2",
            "constant": "φ",
            "text": "V TWo",
            "extern": "two",
            "date_enum": date(year=1984, month=8, day=7),
            "datetime_enum": datetime(1991, 6, 15, 20, 9, 0),
            "duration_enum": timedelta(weeks=2),
            "time_enum": time(hour=9),
            "decimal_enum": Decimal("99.9999"),
            "constant": self.Constants.GOLDEN_RATIO,
        }

    @property
    def values_params(self):
        return {
            "small_pos_int": self.SmallPosIntEnum.VAL2,
            "small_int": "Value -32768",
            "pos_int": 2147483647,
            "int": -2147483648,
            "big_pos_int": "Value 2147483648",
            "big_int": "VAL2",
            "constant": "φ",
            "text": "V TWo",
            "extern": "two",
            "dj_int_enum": 3,
            "dj_text_enum": self.DJTextEnum.A,
            "non_strict_int": 75,
            "non_strict_text": "arbitrary",
            "no_coerce": self.SmallPosIntEnum.VAL2,
        }

    def test_values(self):
        from django.db.models.fields import NOT_PROVIDED

        values1, values2 = super().do_test_values()

        # also test equality symmetry
        self.assertEqual(values1["small_pos_int"], "Value 2")
        self.assertEqual(values1["small_int"], "Value -32768")
        self.assertEqual(values1["pos_int"], 2147483647)
        self.assertEqual(values1["int"], -2147483648)
        self.assertEqual(values1["big_pos_int"], "Value 2147483648")
        self.assertEqual(values1["big_int"], "VAL2")
        self.assertEqual(values1["constant"], "φ")
        self.assertEqual(values1["text"], "V TWo")
        self.assertEqual(values1["extern"], "Two")

        for field in [
            "small_pos_int",
            "small_int",
            "pos_int",
            "int",
            "big_pos_int",
            "big_int",
            "constant",
            "text",
        ]:
            default = self.MODEL_CLASS._meta.get_field(field).default
            if default is NOT_PROVIDED:
                default = None
            self.assertEqual(values2[field], default)

    def test_validate(self):
        tester = super().do_test_validate()

        self.assertTrue(
            tester._meta.get_field("small_int").validate("Value -32768", tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("pos_int").validate(2147483647, tester) is None
        )
        self.assertTrue(tester._meta.get_field("int").validate("VALn1", tester) is None)
        self.assertTrue(
            tester._meta.get_field("big_pos_int").validate("Value 2147483648", tester)
            is None
        )
        self.assertTrue(
            tester._meta.get_field("big_int").validate(self.BigPosIntEnum.VAL2, tester)
            is None
        )
        self.assertTrue(
            tester._meta.get_field("constant").validate("φ", tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("text").validate("default", tester) is None
        )

        self.assertTrue(
            tester._meta.get_field("dj_int_enum").validate(1, tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("dj_text_enum").validate("A", tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("non_strict_int").validate(20, tester) is None
        )

    def test_coerce_to_primitive_error(self):
        """
        Override this base class test because this should work with symmetrical enum.
        """
        create_params = {**self.create_params, "no_coerce": "Value 32767"}

        tester = self.MODEL_CLASS.objects.create(**create_params)
        self.assertEqual(tester.no_coerce, self.SmallPosIntEnum.VAL3)
        self.assertEqual(tester.no_coerce, "Value 32767")

        tester.refresh_from_db()
        self.assertEqual(tester.no_coerce, 32767)

    def test_flag_choice_hashable(self):
        class HashableFlagChoice(FlagChoices):
            READ = 1**2
            WRITE = 2**2
            EXECUTE = 3**2

        self.assertEqual(hash(HashableFlagChoice.READ), hash(1**2))
        self.assertEqual(hash(HashableFlagChoice.WRITE), hash(2**2))
        self.assertEqual(hash(HashableFlagChoice.EXECUTE), hash(3**2))

        test_dict = {
            HashableFlagChoice.READ: "read",
            HashableFlagChoice.WRITE: "write",
            HashableFlagChoice.EXECUTE: "execute",
        }

        self.assertEqual(test_dict[HashableFlagChoice.READ], "read")
        self.assertEqual(test_dict[HashableFlagChoice.WRITE], "write")
        self.assertEqual(test_dict[HashableFlagChoice.EXECUTE], "execute")


# we do this to avoid the base class tests from being collected and re-run in this module
BaseTestChoices = None
