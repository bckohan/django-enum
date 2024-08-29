import pytest

pytest.importorskip("enum_properties")

from tests.test_queries import TestEnumQueries
from tests.enum_prop.models import EnumTester


class TestEnumQueriesProps(TestEnumQueries):
    MODEL_CLASS = EnumTester

    def test_query(self):
        # don't call super b/c referenced types are different

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
            self.MODEL_CLASS.objects.filter(small_pos_int="Value 2").count(), 2
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                small_pos_int=self.SmallPosIntEnum.VAL2.name
            ).count(),
            2,
        )

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                big_pos_int=self.BigPosIntEnum.VAL3
            ).count(),
            2,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                big_pos_int=self.BigPosIntEnum.VAL3.label
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
                constant=self.Constants.GOLDEN_RATIO.name
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

        # test symmetry
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                constant=self.Constants.GOLDEN_RATIO.symbol
            ).count(),
            2,
        )
        self.assertEqual(self.MODEL_CLASS.objects.filter(constant="φ").count(), 2)

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(text=self.TextEnum.VALUE2).count(), 2
        )
        self.assertEqual(len(self.TextEnum.VALUE2.aliases), 3)
        for alias in self.TextEnum.VALUE2.aliases:
            self.assertEqual(self.MODEL_CLASS.objects.filter(text=alias).count(), 2)

        self.assertEqual(self.MODEL_CLASS.objects.filter(extern="One").count(), 2)
        self.assertEqual(self.MODEL_CLASS.objects.filter(extern="Two").count(), 0)

        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, int_field="a")
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, float_field="a")
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, constant="p")
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, big_pos_int="p")
        self.assertRaises(
            ValueError,
            self.MODEL_CLASS.objects.filter,
            big_pos_int=type("WrongType")(),
        )


TestEnumQueries = None
