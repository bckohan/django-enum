from tests.utils import EnumTypeMixin
from django.test import TestCase
from tests.djenum.models import EnumTester


class TestEnumQueries(EnumTypeMixin, TestCase):
    MODEL_CLASS = EnumTester

    def setUp(self):
        self.MODEL_CLASS.objects.all().delete()

        self.MODEL_CLASS.objects.create(
            small_pos_int=self.SmallPosIntEnum.VAL2,
            small_int=self.SmallIntEnum.VAL0,
            pos_int=self.PosIntEnum.VAL1,
            int=self.IntEnum.VALn1,
            big_pos_int=self.BigPosIntEnum.VAL3,
            big_int=self.BigIntEnum.VAL2,
            constant=self.Constants.GOLDEN_RATIO,
            text=self.TextEnum.VALUE2,
            extern=self.ExternEnum.ONE,
        )
        self.MODEL_CLASS.objects.create(
            small_pos_int=self.SmallPosIntEnum.VAL2,
            small_int=self.SmallIntEnum.VAL0,
            pos_int=self.PosIntEnum.VAL1,
            int=self.IntEnum.VALn1,
            big_pos_int=self.BigPosIntEnum.VAL3,
            big_int=self.BigIntEnum.VAL2,
            constant=self.Constants.GOLDEN_RATIO,
            text=self.TextEnum.VALUE2,
            extern=self.ExternEnum.ONE,
        )

        self.MODEL_CLASS.objects.create()

    def test_query(self):
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                small_pos_int=self.SmallPosIntEnum.VAL2
            ).count(),
            2,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                small_pos_int=self.SmallPosIntEnum.VAL2.value
            ).count(),
            2,
        )

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                big_pos_int=self.BigPosIntEnum.VAL3
            ).count(),
            2,
        )
        self.assertEqual(self.MODEL_CLASS.objects.filter(big_pos_int=None).count(), 1)

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                constant=self.Constants.GOLDEN_RATIO
            ).count(),
            2,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                constant=self.Constants.GOLDEN_RATIO.value
            ).count(),
            2,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(constant__isnull=True).count(), 1
        )

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(text=self.TextEnum.VALUE2).count(), 2
        )

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(extern=self.ExternEnum.ONE).count(), 2
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(extern=self.ExternEnum.TWO).count(), 0
        )

        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, int_field="a")
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, float_field="a")
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, constant="Pi")
        self.assertRaises(
            ValueError, self.MODEL_CLASS.objects.filter, big_pos_int="Val3"
        )
        self.assertRaises(
            ValueError, self.MODEL_CLASS.objects.filter, big_pos_int=type("WrongType")()
        )
