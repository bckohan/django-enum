from django.test import TestCase
from decimal import Decimal
from django.core.exceptions import ValidationError


class TestValidatorAdapter(TestCase):
    def test(self):
        from django.core.validators import DecimalValidator

        from django_enum.fields import EnumValidatorAdapter

        validator = DecimalValidator(max_digits=5, decimal_places=2)
        adapted = EnumValidatorAdapter(validator, allow_null=False)
        self.assertEqual(adapted.max_digits, validator.max_digits)
        self.assertEqual(adapted.decimal_places, validator.decimal_places)
        self.assertEqual(adapted, validator)
        self.assertEqual(repr(adapted), f"EnumValidatorAdapter({repr(validator)})")
        ok = Decimal("123.45")
        bad = Decimal("123.456")
        self.assertIsNone(validator(ok))
        self.assertIsNone(adapted(ok))
        self.assertRaises(ValidationError, validator, bad)
        self.assertRaises(ValidationError, adapted, bad)
