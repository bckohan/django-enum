from django.test import TestCase
from decimal import Decimal


class TestEnumConverter(TestCase):
    def test_enum_converter(self):
        from django.urls import reverse
        from django.urls.converters import get_converters

        from tests.converters.urls import TestEnum, record
        from tests.djenum.enums import Constants, DecimalEnum

        converter = get_converters()["TestEnum"]
        self.assertEqual(converter.regex, "1|2")
        self.assertEqual(converter.to_python("1"), TestEnum.A)
        self.assertEqual(converter.to_python("2"), TestEnum.B)
        self.assertEqual(converter.primitive, int)
        self.assertEqual(converter.enum, TestEnum)
        self.assertEqual(converter.prop, "value")

        self.assertEqual(
            reverse("enum1_view", kwargs={"enum": TestEnum.A}), "/converters/1"
        )

        response = self.client.get("/converters/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(record[0], TestEnum.A)

        converter = get_converters()["decimal_enum"]
        self.assertEqual(converter.regex, "0.99|0.999|0.9999|99.9999|999")
        self.assertEqual(converter.to_python("0.999"), DecimalEnum.TWO)
        self.assertEqual(converter.to_python("99.9999"), DecimalEnum.FOUR)
        self.assertEqual(converter.primitive, Decimal)
        self.assertEqual(converter.enum, DecimalEnum)
        self.assertEqual(converter.prop, "value")

        self.assertEqual(
            reverse("decimal_enum_view", kwargs={"enum": DecimalEnum.ONE}),
            "/converters/0.99",
        )

        response = self.client.get("/converters/0.99")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(record[1], DecimalEnum.ONE)

        converter = get_converters()["Constants"]
        self.assertEqual(converter.regex, "Pi|Euler's Number|Golden Ratio")
        self.assertEqual(converter.to_python("Golden Ratio"), Constants.GOLDEN_RATIO)
        self.assertEqual(converter.to_python("Euler's Number"), Constants.e)
        self.assertEqual(converter.to_python("Pi"), Constants.PI)
        self.assertEqual(converter.primitive, float)
        self.assertEqual(converter.enum, Constants)
        self.assertEqual(converter.prop, "label")

        self.assertEqual(
            reverse("constants_view", kwargs={"enum": Constants.GOLDEN_RATIO}),
            "/converters/Golden%20Ratio",
        )

        response = self.client.get("/converters/Euler's Number")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(record[2], Constants.e)
