from django.test import TestCase
from django.core.exceptions import ValidationError
from django_enum import EnumField
from tests.djenum.models import EnumTester


class MiscOffNominalTests(TestCase):
    def test_field_def_errors(self):
        from django.db.models import Model

        with self.assertRaises(ValueError):

            class TestModel(Model):
                enum = EnumField()

    def test_full_clean_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            en = EnumTester(text="wrong")
            en.full_clean()

        with self.assertRaises(ValidationError):
            EnumTester(text="").full_clean()

    def test_variable_primitive_type(self):
        from enum import Enum

        from django.db.models import Model

        from django_enum.utils import determine_primitive

        class MultiPrimitive(Enum):
            VAL1 = 1
            VAL2 = "2"
            VAL3 = 3.0
            VAL4 = b"4"

        self.assertIsNone(determine_primitive(MultiPrimitive))

        with self.assertRaises(ValueError):

            class TestModel(Model):
                enum = EnumField(MultiPrimitive)

        with self.assertRaises(ValueError):
            """
            2 is not symmetrically convertable float<->str
            """

            class TestModel(Model):
                enum = EnumField(MultiPrimitive, primitive=float)

    def test_unsupported_primitive(self):
        from enum import Enum

        from django_enum.utils import determine_primitive

        class MyPrimitive:
            pass

        class WeirdPrimitive(Enum):
            VAL1 = MyPrimitive()
            VAL2 = MyPrimitive()
            VAL3 = MyPrimitive()

        self.assertEqual(determine_primitive(WeirdPrimitive), MyPrimitive)

        with self.assertRaises(NotImplementedError):
            EnumField(WeirdPrimitive)

    def test_bit_length_override(self):
        from enum import IntFlag

        class IntEnum(IntFlag):
            VAL1 = 2**0
            VAL2 = 2**2
            VAL3 = 2**3
            VAL8 = 2**8

        with self.assertRaises(AssertionError):
            EnumField(IntEnum, bit_length=7)

        field = EnumField(IntEnum, bit_length=12)
        self.assertEqual(field.bit_length, 12)

    def test_no_value_enum(self):
        from enum import Enum

        from django_enum.utils import determine_primitive

        class EmptyEnum(Enum):
            pass

        self.assertIsNone(determine_primitive(EmptyEnum))

        with self.assertRaises(ValueError):
            EnumField(EmptyEnum)

    def test_copy_field(self):
        from copy import copy, deepcopy
        from enum import Enum

        class BasicEnum(Enum):
            VAL1 = "1"
            VAL2 = "2"
            VAL3 = "3"

        field = EnumField(BasicEnum)
        field2 = deepcopy(field)
        field3 = copy(field)

        self.assertEqual(field.enum, field2.enum, field3.enum)


class TestEmptyEnumValues(TestCase):
    def test_none_enum_values(self):
        # TODO??
        pass
