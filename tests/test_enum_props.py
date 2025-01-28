import pytest

pytest.importorskip("enum_properties")

from tests.utils import EnumTypeMixin
from django.test import TestCase
from tests.enum_prop.models import EnumTester
from enum_properties import s
from django.db import transaction
from django_enum.forms import EnumChoiceField
from django_enum.choices import TextChoices
from tests.enum_prop.enums import PrecedenceTest


class TestEnumPropertiesIntegration(EnumTypeMixin, TestCase):
    MODEL_CLASS = EnumTester

    def test_properties_and_symmetry(self):
        self.assertEqual(self.Constants.PI.symbol, "π")
        self.assertEqual(self.Constants.e.symbol, "e")
        self.assertEqual(self.Constants.GOLDEN_RATIO.symbol, "φ")

        # test symmetry
        self.assertEqual(self.Constants.PI, self.Constants("π"))
        self.assertEqual(self.Constants.e, self.Constants("e"))
        self.assertEqual(self.Constants.GOLDEN_RATIO, self.Constants("φ"))

        self.assertEqual(self.Constants.PI, self.Constants("PI"))
        self.assertEqual(self.Constants.e, self.Constants("e"))
        self.assertEqual(self.Constants.GOLDEN_RATIO, self.Constants("GOLDEN_RATIO"))

        self.assertEqual(self.Constants.PI, self.Constants("Pi"))
        self.assertEqual(self.Constants.e, self.Constants("Euler's Number"))
        self.assertEqual(self.Constants.GOLDEN_RATIO, self.Constants("Golden Ratio"))

        self.assertEqual(self.TextEnum.VALUE1.version, 0)
        self.assertEqual(self.TextEnum.VALUE2.version, 1)
        self.assertEqual(self.TextEnum.VALUE3.version, 2)
        self.assertEqual(self.TextEnum.DEFAULT.version, 3)

        self.assertEqual(self.TextEnum.VALUE1.help, "Some help text about value1.")
        self.assertEqual(self.TextEnum.VALUE2.help, "Some help text about value2.")
        self.assertEqual(self.TextEnum.VALUE3.help, "Some help text about value3.")
        self.assertEqual(self.TextEnum.DEFAULT.help, "Some help text about default.")

        self.assertEqual(self.TextEnum.VALUE1, self.TextEnum("VALUE1"))
        self.assertEqual(self.TextEnum.VALUE2, self.TextEnum("VALUE2"))
        self.assertEqual(self.TextEnum.VALUE3, self.TextEnum("VALUE3"))
        self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum("DEFAULT"))

        self.assertEqual(self.TextEnum.VALUE1, self.TextEnum("Value1"))
        self.assertEqual(self.TextEnum.VALUE2, self.TextEnum("Value2"))
        self.assertEqual(self.TextEnum.VALUE3, self.TextEnum("Value3"))
        self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum("Default"))

        # test asymmetry
        self.assertRaises(ValueError, self.TextEnum, 0)
        self.assertRaises(ValueError, self.TextEnum, 1)
        self.assertRaises(ValueError, self.TextEnum, 2)
        self.assertRaises(ValueError, self.TextEnum, 3)

        # test asymmetry
        self.assertRaises(ValueError, self.TextEnum, "Some help text about value1.")
        self.assertRaises(ValueError, self.TextEnum, "Some help text about value2.")
        self.assertRaises(ValueError, self.TextEnum, "Some help text about value3.")
        self.assertRaises(ValueError, self.TextEnum, "Some help text about default.")

        # test basic case insensitive iterable symmetry
        self.assertEqual(self.TextEnum.VALUE1, self.TextEnum("val1"))
        self.assertEqual(self.TextEnum.VALUE1, self.TextEnum("v1"))
        self.assertEqual(self.TextEnum.VALUE1, self.TextEnum("v one"))
        self.assertEqual(self.TextEnum.VALUE1, self.TextEnum("VaL1"))
        self.assertEqual(self.TextEnum.VALUE1, self.TextEnum("V1"))
        self.assertEqual(self.TextEnum.VALUE1, self.TextEnum("v ONE"))

        self.assertEqual(self.TextEnum.VALUE2, self.TextEnum("val22"))
        self.assertEqual(self.TextEnum.VALUE2, self.TextEnum("v2"))
        self.assertEqual(self.TextEnum.VALUE2, self.TextEnum("v two"))
        self.assertEqual(self.TextEnum.VALUE2, self.TextEnum("VaL22"))
        self.assertEqual(self.TextEnum.VALUE2, self.TextEnum("V2"))
        self.assertEqual(self.TextEnum.VALUE2, self.TextEnum("v TWo"))

        self.assertEqual(self.TextEnum.VALUE3, self.TextEnum("val333"))
        self.assertEqual(self.TextEnum.VALUE3, self.TextEnum("v3"))
        self.assertEqual(self.TextEnum.VALUE3, self.TextEnum("v three"))
        self.assertEqual(self.TextEnum.VALUE3, self.TextEnum("VaL333"))
        self.assertEqual(self.TextEnum.VALUE3, self.TextEnum("V333"))
        self.assertEqual(self.TextEnum.VALUE3, self.TextEnum("v THRee"))

        self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum("default"))
        self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum("DeFaULT"))
        self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum("DEfacTO"))
        self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum("defacto"))
        self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum("NONE"))
        self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum("none"))

    def test_value_type_coercion(self):
        """test basic value coercion from str"""
        self.assertEqual(
            self.Constants.PI,
            self.Constants("3.14159265358979323846264338327950288"),
        )
        self.assertEqual(self.Constants.e, self.Constants("2.71828"))
        self.assertEqual(
            self.Constants.GOLDEN_RATIO,
            self.Constants("1.61803398874989484820458683436563811"),
        )

        self.assertEqual(self.SmallPosIntEnum.VAL1, self.SmallPosIntEnum("0"))
        self.assertEqual(self.SmallPosIntEnum.VAL2, self.SmallPosIntEnum("2"))
        self.assertEqual(self.SmallPosIntEnum.VAL3, self.SmallPosIntEnum("32767"))

        self.assertEqual(self.SmallIntEnum.VALn1, self.SmallIntEnum("-32768"))
        self.assertEqual(self.SmallIntEnum.VAL0, self.SmallIntEnum("0"))
        self.assertEqual(self.SmallIntEnum.VAL1, self.SmallIntEnum("1"))
        self.assertEqual(self.SmallIntEnum.VAL2, self.SmallIntEnum("2"))
        self.assertEqual(self.SmallIntEnum.VAL3, self.SmallIntEnum("32767"))

        self.assertEqual(self.IntEnum.VALn1, self.IntEnum("-2147483648"))
        self.assertEqual(self.IntEnum.VAL0, self.IntEnum("0"))
        self.assertEqual(self.IntEnum.VAL1, self.IntEnum("1"))
        self.assertEqual(self.IntEnum.VAL2, self.IntEnum("2"))
        self.assertEqual(self.IntEnum.VAL3, self.IntEnum("2147483647"))

        self.assertEqual(self.PosIntEnum.VAL0, self.PosIntEnum("0"))
        self.assertEqual(self.PosIntEnum.VAL1, self.PosIntEnum("1"))
        self.assertEqual(self.PosIntEnum.VAL2, self.PosIntEnum("2"))
        self.assertEqual(self.PosIntEnum.VAL3, self.PosIntEnum("2147483647"))

        self.assertEqual(self.BigPosIntEnum.VAL0, self.BigPosIntEnum("0"))
        self.assertEqual(self.BigPosIntEnum.VAL1, self.BigPosIntEnum("1"))
        self.assertEqual(self.BigPosIntEnum.VAL2, self.BigPosIntEnum("2"))
        self.assertEqual(self.BigPosIntEnum.VAL3, self.BigPosIntEnum("2147483648"))

        self.assertEqual(self.BigIntEnum.VAL0, self.BigIntEnum("-2147483649"))
        self.assertEqual(self.BigIntEnum.VAL1, self.BigIntEnum("1"))
        self.assertEqual(self.BigIntEnum.VAL2, self.BigIntEnum("2"))
        self.assertEqual(self.BigIntEnum.VAL3, self.BigIntEnum("2147483648"))

    def test_symmetric_type_coercion(self):
        """test that symmetric properties have types coerced"""
        self.assertEqual(self.BigIntEnum.VAL0, self.BigIntEnum(self.BigPosIntEnum.VAL0))
        self.assertEqual(self.BigIntEnum.VAL1, self.BigIntEnum(self.BigPosIntEnum.VAL1))
        self.assertEqual(self.BigIntEnum.VAL2, self.BigIntEnum(self.BigPosIntEnum.VAL2))
        self.assertEqual(self.BigIntEnum.VAL3, self.BigIntEnum(self.BigPosIntEnum.VAL3))

        self.assertEqual(self.BigIntEnum.VAL0, self.BigIntEnum(0))
        self.assertEqual(self.BigIntEnum.VAL0, self.BigIntEnum("0"))

    def test_no_labels(self):
        """
        Tests that an enum without labels and with properties works as expected
        """

        class NoLabels(TextChoices, s("not_a_label")):
            VAL1 = "E1", "E1 Label"
            VAL2 = "E2", "E2 Label"

        self.assertEqual(NoLabels.VAL1.label, "VAL1".title())
        self.assertEqual(NoLabels.VAL1.name, "VAL1")
        self.assertEqual(NoLabels.VAL2.label, "VAL2".title())
        self.assertEqual(NoLabels.VAL2.name, "VAL2")
        self.assertEqual(NoLabels.VAL1.not_a_label, "E1 Label")
        self.assertEqual(NoLabels.VAL2.not_a_label, "E2 Label")

        self.assertEqual(NoLabels.VAL1, NoLabels("E1 Label"))
        self.assertEqual(NoLabels.VAL2, NoLabels("E2 Label"))

        self.assertEqual(NoLabels.VAL1, NoLabels("VAL1"))
        self.assertEqual(NoLabels.VAL1, NoLabels("Val1"))

        self.assertEqual(NoLabels.VAL1, NoLabels("E1"))
        self.assertEqual(NoLabels.VAL2, NoLabels("E2"))

        class NoLabelsOrProps(TextChoices):
            VAL1 = "E1"
            VAL2 = "E2"

        self.assertEqual(NoLabelsOrProps.VAL1.label, "VAL1".title())
        self.assertEqual(NoLabelsOrProps.VAL1.name, "VAL1")
        self.assertEqual(NoLabelsOrProps.VAL2.label, "VAL2".title())
        self.assertEqual(NoLabelsOrProps.VAL2.name, "VAL2")

        self.assertEqual(NoLabelsOrProps.VAL1, NoLabelsOrProps("VAL1"))
        self.assertEqual(NoLabelsOrProps.VAL2, NoLabelsOrProps("Val2"))

        self.assertEqual(NoLabelsOrProps.VAL1, NoLabelsOrProps("E1"))
        self.assertEqual(NoLabelsOrProps.VAL2, NoLabelsOrProps("E2"))

    def test_saving(self):
        """
        Test that enum values can be saved directly.
        """
        tester = self.MODEL_CLASS.objects.create(
            small_pos_int=self.SmallPosIntEnum.VAL2,
            small_int=self.SmallIntEnum.VAL0,
            pos_int=self.PosIntEnum.VAL1,
            int=self.IntEnum.VALn1,
            big_pos_int=self.BigPosIntEnum.VAL3,
            big_int=self.BigIntEnum.VAL2,
            date_enum=self.DateEnum.BRIAN,
            datetime_enum=self.DateTimeEnum.PINATUBO,
            duration_enum=self.DurationEnum.FORTNIGHT,
            time_enum=self.TimeEnum.LUNCH,
            decimal_enum=self.DecimalEnum.THREE,
            constant=self.Constants.GOLDEN_RATIO,
            text=self.TextEnum.VALUE2,
            extern=self.ExternEnum.ONE,
        )

        self.assertEqual(tester.small_pos_int, self.SmallPosIntEnum.VAL2)
        self.assertEqual(tester.small_int, self.SmallIntEnum.VAL0)
        self.assertEqual(tester.pos_int, self.PosIntEnum.VAL1)
        self.assertEqual(tester.int, self.IntEnum.VALn1)
        self.assertEqual(tester.big_pos_int, self.BigPosIntEnum.VAL3)
        self.assertEqual(tester.big_int, self.BigIntEnum.VAL2)
        self.assertEqual(tester.constant, self.Constants.GOLDEN_RATIO)
        self.assertEqual(tester.text, self.TextEnum.VALUE2)
        self.assertEqual(tester.extern, self.ExternEnum.ONE)
        self.assertEqual(tester.date_enum, self.DateEnum.BRIAN)
        self.assertEqual(tester.datetime_enum, self.DateTimeEnum.PINATUBO)
        self.assertEqual(tester.duration_enum, self.DurationEnum.FORTNIGHT)
        self.assertEqual(tester.time_enum, self.TimeEnum.LUNCH)
        self.assertEqual(tester.decimal_enum, self.DecimalEnum.THREE)

        tester.small_pos_int = self.SmallPosIntEnum.VAL1
        tester.small_int = self.SmallIntEnum.VAL2
        tester.pos_int = self.PosIntEnum.VAL0
        tester.int = self.IntEnum.VAL1
        tester.big_pos_int = self.BigPosIntEnum.VAL2
        tester.big_int = self.BigIntEnum.VAL1
        tester.constant = self.Constants.PI
        tester.text = self.TextEnum.VALUE3
        tester.extern = self.ExternEnum.TWO

        tester.save()

        self.assertEqual(tester.small_pos_int, self.SmallPosIntEnum.VAL1)
        self.assertEqual(tester.small_int, self.SmallIntEnum.VAL2)
        self.assertEqual(tester.pos_int, self.PosIntEnum.VAL0)
        self.assertEqual(tester.int, self.IntEnum.VAL1)
        self.assertEqual(tester.big_pos_int, self.BigPosIntEnum.VAL2)
        self.assertEqual(tester.big_int, self.BigIntEnum.VAL1)
        self.assertEqual(tester.constant, self.Constants.PI)
        self.assertEqual(tester.text, self.TextEnum.VALUE3)
        self.assertEqual(tester.extern, self.ExternEnum.TWO)

        tester.refresh_from_db()

        self.assertEqual(tester.small_pos_int, self.SmallPosIntEnum.VAL1)
        self.assertEqual(tester.small_int, self.SmallIntEnum.VAL2)
        self.assertEqual(tester.pos_int, self.PosIntEnum.VAL0)
        self.assertEqual(tester.int, self.IntEnum.VAL1)
        self.assertEqual(tester.big_pos_int, self.BigPosIntEnum.VAL2)
        self.assertEqual(tester.big_int, self.BigIntEnum.VAL1)
        self.assertEqual(tester.constant, self.Constants.PI)
        self.assertEqual(tester.text, self.TextEnum.VALUE3)
        self.assertEqual(tester.extern, self.ExternEnum.TWO)

        tester.small_pos_int = "32767"
        tester.small_int = -32768
        tester.pos_int = 2147483647
        tester.int = -2147483648
        tester.big_pos_int = 2147483648
        tester.big_int = -2147483649
        tester.constant = "2.71828"
        tester.text = "D"
        tester.extern = "Three"

        tester.save()
        tester.refresh_from_db()

        self.assertEqual(tester.small_pos_int, 32767)
        self.assertEqual(tester.small_int, -32768)
        self.assertEqual(tester.pos_int, 2147483647)
        self.assertEqual(tester.int, -2147483648)
        self.assertEqual(tester.big_pos_int, 2147483648)
        self.assertEqual(tester.big_int, -2147483649)
        self.assertEqual(tester.constant, 2.71828)
        self.assertEqual(tester.text, "D")
        self.assertEqual(tester.extern, self.ExternEnum.THREE)

        with transaction.atomic():
            tester.text = "not valid"
            self.assertRaises(ValueError, tester.save)
        tester.refresh_from_db()

        with transaction.atomic():
            tester.text = type("WrongType")()
            self.assertRaises(ValueError, tester.save)
        tester.refresh_from_db()

        with transaction.atomic():
            tester.text = 1
            self.assertRaises(ValueError, tester.save)
        tester.refresh_from_db()

        # fields with choices are more permissive - choice check does not happen on basic save
        with transaction.atomic():
            tester.char_choice = "not valid"
            tester.save()
            # self.assertRaises(ValidationError, tester.save)
        tester.refresh_from_db()

        with transaction.atomic():
            tester.char_choice = 5
            tester.save()
            # self.assertRaises(ValueError, tester.save)
        tester.refresh_from_db()

        with transaction.atomic():
            tester.int_choice = 5
            tester.save()
            # self.assertRaises(ValueError, tester.save)
        tester.refresh_from_db()
        #####################################################################################

        with transaction.atomic():
            tester.int_choice = "a"
            self.assertRaises(ValueError, tester.save)
        tester.refresh_from_db()

        tester.text = None
        tester.save()
        self.assertEqual(tester.text, None)


class TestSymmetricEmptyValEquivalency(TestCase):
    def test(self):
        from enum_properties import EnumProperties

        class EmptyEqEnum(TextChoices, s("prop", case_fold=True)):
            A = "A", "ok"
            B = "B", "none"

        form_field = EnumChoiceField(enum=EmptyEqEnum)
        self.assertTrue(None in form_field.empty_values)

        class EmptyEqEnum(TextChoices, s("prop", case_fold=True)):
            A = "A", "ok"
            B = "B", None

        form_field = EnumChoiceField(enum=EmptyEqEnum)
        self.assertTrue(None in form_field.empty_values)

        class EmptyEqEnum(TextChoices, s("prop", match_none=True)):
            A = "A", "ok"
            B = "B", None

        form_field = EnumChoiceField(enum=EmptyEqEnum)
        self.assertTrue(None not in form_field.empty_values)

        # version 1.5.0 of enum_properties changed the default symmetricity
        # of none values.
        from enum_properties import VERSION

        match_none = {} if VERSION < (1, 5, 0) else {"match_none": True}

        class EmptyEqEnum(EnumProperties, s("label", case_fold=True)):
            A = "A", "A Label"
            B = None, "B Label"

        try:
            form_field = EnumChoiceField(enum=EmptyEqEnum)
        except Exception as err:  # pragma: no cover
            self.fail(
                "EnumChoiceField() raised value error with alternativeempty_value set."
            )

        self.assertTrue(None not in form_field.empty_values)

        class EmptyEqEnum(
            EnumProperties, s("label", case_fold=True), s("prop", match_none=True)
        ):
            A = "A", "A Label", 4
            B = "B", "B Label", None
            C = "C", "C Label", ""

        try:
            form_field = EnumChoiceField(enum=EmptyEqEnum)
        except Exception as err:  # pragma: no cover
            self.fail(
                "EnumChoiceField() raised value error with alternativeempty_value set."
            )

        # this is pathological
        self.assertTrue(None not in form_field.empty_values)
        self.assertTrue("" not in form_field.empty_values)
        self.assertTrue(form_field.empty_value == form_field.empty_values[0])

        class EmptyEqEnum2(TextChoices, s("prop", case_fold=True, **match_none)):
            A = "A", [None, "", ()]
            B = "B", "ok"

        field = EnumChoiceField(enum=EmptyEqEnum2, empty_values=[None, "", ()])
        self.assertEqual(field.empty_values, [None, "", ()])
        self.assertEqual(field.empty_value, "")

        field2 = EnumChoiceField(enum=EmptyEqEnum2, empty_value=0)
        self.assertEqual(field2.empty_values, [0, [], {}])
        self.assertEqual(field2.empty_value, 0)

        field3 = EnumChoiceField(enum=EmptyEqEnum2, empty_values=[None, ()])
        self.assertEqual(field3.empty_values, [None, ()])
        self.assertEqual(field3.empty_value, None)

        self.assertRaises(
            ValueError,
            EnumChoiceField,
            enum=EmptyEqEnum2,
            empty_value=0,
            empty_values=[None, "", ()],
        )

        try:

            class EmptyEqEnum2(TextChoices, s("prop", case_fold=True)):
                A = "A", [None, "", ()]
                B = "B", "ok"

            EnumChoiceField(
                enum=EmptyEqEnum2, empty_value=0, empty_values=[0, None, "", ()]
            )
        except Exception:  # pragma: no cover
            self.fail(
                "EnumChoiceField() raised value error with alternativeempty_value set."
            )


class PrecedenceTestCase(TestCase):
    def test_precedence(self):
        """
        test that symmetric properties with non-hashable iterable values treat each iterable as a separate
        symmetric value
        """
        self.assertEqual(PrecedenceTest.P1, PrecedenceTest(0))
        self.assertEqual(PrecedenceTest.P2, PrecedenceTest(1))
        self.assertEqual(PrecedenceTest.P3, PrecedenceTest(2))
        self.assertEqual(PrecedenceTest.P4, PrecedenceTest(3))

        self.assertEqual(PrecedenceTest.P1, PrecedenceTest("Precedence 1"))
        self.assertEqual(PrecedenceTest.P2, PrecedenceTest("Precedence 2"))
        self.assertEqual(PrecedenceTest.P3, PrecedenceTest("Precedence 3"))
        self.assertEqual(PrecedenceTest.P4, PrecedenceTest("Precedence 4"))

        # type match takes precedence
        self.assertEqual(PrecedenceTest.P3, PrecedenceTest("1"))
        self.assertEqual(PrecedenceTest.P1, PrecedenceTest("0.4"))
        self.assertEqual(PrecedenceTest.P2, PrecedenceTest("0.3"))

        self.assertEqual(PrecedenceTest.P1, PrecedenceTest(0.1))
        self.assertEqual(PrecedenceTest.P2, PrecedenceTest(0.2))
        self.assertEqual(PrecedenceTest.P1, PrecedenceTest("0.1"))
        self.assertEqual(PrecedenceTest.P2, PrecedenceTest("0.2"))
        self.assertEqual(PrecedenceTest.P3, PrecedenceTest(0.3))
        self.assertEqual(PrecedenceTest.P4, PrecedenceTest(0.4))

        self.assertEqual(PrecedenceTest.P1, PrecedenceTest("First"))
        self.assertEqual(PrecedenceTest.P2, PrecedenceTest("Second"))
        self.assertEqual(PrecedenceTest.P3, PrecedenceTest("Third"))
        self.assertEqual(PrecedenceTest.P4, PrecedenceTest("Fourth"))

        # lower priority case insensitive match
        self.assertEqual(PrecedenceTest.P4, PrecedenceTest("FIRST"))
        self.assertEqual(PrecedenceTest.P3, PrecedenceTest("SECOND"))
        self.assertEqual(PrecedenceTest.P2, PrecedenceTest("THIRD"))
        self.assertEqual(PrecedenceTest.P1, PrecedenceTest("FOURTH"))

        self.assertEqual(PrecedenceTest.P4, PrecedenceTest(4))
        self.assertEqual(PrecedenceTest.P4, PrecedenceTest("4"))
