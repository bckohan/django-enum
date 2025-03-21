from django.test import TestCase
from django_enum.utils import get_set_bits, get_set_values, decompose


class UtilsTests(TestCase):
    def test_get_set_values(self):
        from tests.djenum.enums import SmallPositiveFlagEnum

        self.assertEqual(
            get_set_values(None),
            [],
        )

        self.assertEqual(
            get_set_values(SmallPositiveFlagEnum.ONE | SmallPositiveFlagEnum.THREE),
            [SmallPositiveFlagEnum.ONE.value, SmallPositiveFlagEnum.THREE.value],
        )
        self.assertEqual(
            get_set_values(
                int((SmallPositiveFlagEnum.ONE | SmallPositiveFlagEnum.THREE).value)
            ),
            [SmallPositiveFlagEnum.ONE.value, SmallPositiveFlagEnum.THREE.value],
        )

        self.assertEqual(
            get_set_values(
                SmallPositiveFlagEnum.TWO | SmallPositiveFlagEnum.FIVE,
            ),
            [SmallPositiveFlagEnum.TWO.value, SmallPositiveFlagEnum.FIVE.value],
        )

        self.assertEqual(
            get_set_values(SmallPositiveFlagEnum.FOUR),
            [SmallPositiveFlagEnum.FOUR.value],
        )

        self.assertEqual(get_set_values(SmallPositiveFlagEnum(0)), [])

        self.assertEqual(get_set_values(int(SmallPositiveFlagEnum(0))), [])

        self.assertEqual(get_set_values(0), [])

    def test_get_set_bits(self):
        from tests.djenum.enums import SmallPositiveFlagEnum

        self.assertEqual(
            get_set_bits(None),
            [],
        )

        self.assertEqual(
            get_set_bits(SmallPositiveFlagEnum.ONE | SmallPositiveFlagEnum.THREE),
            [10, 12],
        )
        self.assertEqual(
            get_set_bits(
                int((SmallPositiveFlagEnum.ONE | SmallPositiveFlagEnum.THREE).value)
            ),
            [10, 12],
        )

        self.assertEqual(
            get_set_bits(
                SmallPositiveFlagEnum.TWO | SmallPositiveFlagEnum.FIVE,
            ),
            [11, 14],
        )

        self.assertEqual(get_set_bits(SmallPositiveFlagEnum.FOUR), [13])

        self.assertEqual(get_set_bits(SmallPositiveFlagEnum(0)), [])

        self.assertEqual(get_set_bits(int(SmallPositiveFlagEnum(0))), [])

        self.assertEqual(get_set_bits(0), [])

    def test_decompose(self):
        from tests.djenum.enums import SmallPositiveFlagEnum

        self.assertEqual(decompose(None), [])

        self.assertEqual(
            decompose(SmallPositiveFlagEnum.ONE | SmallPositiveFlagEnum.THREE),
            [SmallPositiveFlagEnum.ONE, SmallPositiveFlagEnum.THREE],
        )

        self.assertEqual(
            decompose(
                SmallPositiveFlagEnum.TWO | SmallPositiveFlagEnum.FIVE,
            ),
            [SmallPositiveFlagEnum.TWO, SmallPositiveFlagEnum.FIVE],
        )

        self.assertEqual(
            decompose(SmallPositiveFlagEnum.FOUR), [SmallPositiveFlagEnum.FOUR]
        )

        self.assertEqual(decompose(SmallPositiveFlagEnum(0)), [])

        self.assertEqual(decompose(int(SmallPositiveFlagEnum(0))), [])

        self.assertEqual(decompose(0), [])
