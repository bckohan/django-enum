from django.test import TestCase
from django_enum.utils import get_set_bits


class UtilsTests(TestCase):
    def test_get_set_bits(self):
        from tests.djenum.enums import SmallPositiveFlagEnum

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
