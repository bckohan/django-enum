from tests.utils import EnumTypeMixin
from django.test import TestCase

from tests.djenum.models import EnumTester, EnumFlagTester
from django.db.models.fields import *
from django_enum.fields import *


class TestFieldTypeResolution(EnumTypeMixin, TestCase):
    MODEL_CLASS = EnumTester
    MODEL_FLAG_CLASS = EnumFlagTester

    def test_base_fields(self):
        """
        Test that the Enum metaclass picks the correct database field type for each enum.
        """
        from django.db.models import (
            BigIntegerField,
            BinaryField,
            CharField,
            DateField,
            DateTimeField,
            DecimalField,
            DurationField,
            FloatField,
            IntegerField,
            PositiveBigIntegerField,
            PositiveIntegerField,
            PositiveSmallIntegerField,
            SmallIntegerField,
            TimeField,
        )

        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("small_int"), SmallIntegerField
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("small_pos_int"), PositiveSmallIntegerField
        )
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("int"), IntegerField)
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("pos_int"), PositiveIntegerField
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("big_int"), BigIntegerField
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("big_pos_int"), PositiveBigIntegerField
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("extern"), PositiveSmallIntegerField
        )
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("text"), CharField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("constant"), FloatField)

        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("small_neg"), SmallIntegerField
        )
        self.assertNotIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("small_neg"), FlagField
        )
        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("small_pos"),
            PositiveSmallIntegerField,
        )
        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("small_pos"), SmallIntegerFlagField
        )

        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("neg"), IntegerField
        )
        self.assertNotIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("neg"), FlagField
        )
        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("pos"), PositiveIntegerField
        )
        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("pos"), IntegerFlagField
        )

        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("big_neg"), BigIntegerField
        )
        self.assertNotIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("big_neg"), FlagField
        )
        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("big_pos"), PositiveBigIntegerField
        )
        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("big_pos"), BigIntegerFlagField
        )

        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("extra_big_neg"),
            EnumExtraBigIntegerField,
        )
        self.assertNotIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("extra_big_neg"), FlagField
        )
        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("extra_big_neg"), BinaryField
        )
        self.assertIsInstance(
            self.MODEL_FLAG_CLASS._meta.get_field("extra_big_pos"),
            ExtraBigIntegerFlagField,
        )

        self.assertEqual(self.MODEL_CLASS._meta.get_field("small_int").primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("small_int").bit_length, 16)
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("small_pos_int").primitive, int
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("small_pos_int").bit_length, 15
        )
        self.assertEqual(self.MODEL_CLASS._meta.get_field("pos_int").primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("pos_int").bit_length, 31)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("int").primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("int").bit_length, 32)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("big_int").primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("big_pos_int").primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("big_pos_int").bit_length, 32)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("big_int").bit_length, 32)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("extern").primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("text").primitive, str)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("constant").primitive, float)

        self.assertEqual(
            self.MODEL_FLAG_CLASS._meta.get_field("small_neg").primitive, int
        )
        self.assertEqual(
            self.MODEL_FLAG_CLASS._meta.get_field("small_pos").primitive, int
        )

        self.assertEqual(self.MODEL_FLAG_CLASS._meta.get_field("neg").primitive, int)
        self.assertEqual(self.MODEL_FLAG_CLASS._meta.get_field("pos").primitive, int)

        self.assertEqual(
            self.MODEL_FLAG_CLASS._meta.get_field("big_neg").primitive, int
        )
        self.assertEqual(
            self.MODEL_FLAG_CLASS._meta.get_field("big_pos").primitive, int
        )
        self.assertEqual(
            self.MODEL_FLAG_CLASS._meta.get_field("extra_big_neg").primitive, int
        )
        self.assertEqual(
            self.MODEL_FLAG_CLASS._meta.get_field("extra_big_pos").primitive, int
        )

        # eccentric enums
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("date_enum"), DateField)
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("datetime_enum"), DateTimeField
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("duration_enum"), DurationField
        )
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("time_enum"), TimeField)
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("decimal_enum"), DecimalField
        )
        self.assertEqual(self.MODEL_CLASS._meta.get_field("decimal_enum").max_digits, 7)
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("decimal_enum").decimal_places, 4
        )

        self.assertEqual(self.MODEL_CLASS._meta.get_field("date_enum").primitive, date)
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("datetime_enum").primitive, datetime
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("duration_enum").primitive, timedelta
        )
        self.assertEqual(self.MODEL_CLASS._meta.get_field("time_enum").primitive, time)
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("decimal_enum").primitive, Decimal
        )
        #

        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("small_int"), EnumField)
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("small_pos_int"), EnumField
        )
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("pos_int"), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("big_int"), EnumField)
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("big_pos_int"), EnumField
        )
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("extern"), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("text"), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("constant"), EnumField)

        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("date_enum"), EnumField)
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("datetime_enum"), EnumField
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("duration_enum"), EnumField
        )
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field("time_enum"), EnumField)
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("decimal_enum"), EnumField
        )

        tester = self.MODEL_CLASS.objects.create()

        self.assertEqual(tester.small_int, tester._meta.get_field("small_int").default)
        self.assertEqual(tester.small_int, self.SmallIntEnum.VAL3)
        self.assertIsNone(tester.small_pos_int)
        self.assertIsInstance(tester._meta.get_field("int"), IntegerField)
        self.assertIsNone(tester.int)

        self.assertEqual(tester.pos_int, tester._meta.get_field("pos_int").default)
        self.assertEqual(tester.pos_int, self.PosIntEnum.VAL3)

        self.assertEqual(tester.big_int, tester._meta.get_field("big_int").default)
        self.assertEqual(tester.big_int, self.BigIntEnum.VAL0)

        self.assertIsNone(tester.big_pos_int)

        self.assertIsInstance(tester._meta.get_field("constant"), FloatField)
        self.assertIsNone(tester.constant)

        self.assertIsInstance(tester._meta.get_field("text"), CharField)
        self.assertEqual(tester._meta.get_field("text").max_length, 4)
        self.assertIsNone(tester.text)

        self.assertIsNone(tester.extern)
