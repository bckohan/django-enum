from django import VERSION as django_version
import pytest

if django_version[0:2] < (5, 0):
    pytest.skip(reason="Requires Django >= 5.0", allow_module_level=True)

from tests.utils import EnumTypeMixin
from django.test import TestCase
from tests.db_default.models import DBDefaultTester
from django.db import connection


class DBDefaultTests(EnumTypeMixin, TestCase):
    MODEL_CLASS = DBDefaultTester

    @property
    def defaults(self):
        return {
            "small_pos_int": None,
            "small_int": self.SmallIntEnum.VAL3,
            "small_int_shadow": self.SmallIntEnum.VAL3,
            "pos_int": self.PosIntEnum.VAL3,
            "int": self.IntEnum.VALn1,
            "big_pos_int": None,
            "big_int": self.BigIntEnum.VAL0,
            "constant": self.Constants.GOLDEN_RATIO,
            "char_field": "db_default",
            "doubled_char_field": "default",
            "text": "",
            "doubled_text": "",
            "doubled_text_strict": self.TextEnum.DEFAULT,
            "extern": self.ExternEnum.THREE,
            "dj_int_enum": self.DJIntEnum.ONE,
            "dj_text_enum": self.DJTextEnum.A,
            "non_strict_int": 5,
            "non_strict_text": "arbitrary",
            "no_coerce": 2,
            "no_coerce_value": 32767,
            "no_coerce_none": None,
        }

    def test_db_defaults(self):
        obj = DBDefaultTester.objects.create()
        # TODO - there seems to be a mysql bug here where DatabaseDefaults
        # are not refreshed from the db after creation - works on all other platforms
        if connection.vendor == "mysql":
            obj.refresh_from_db()

        for field, value in self.defaults.items():
            obj_field = DBDefaultTester._meta.get_field(field)
            obj_value = getattr(obj, field)
            self.assertEqual(obj_value, value)
            from django_enum.fields import EnumField

            if (
                isinstance(obj_field, EnumField)
                and obj_field.strict
                and obj_field.coerce
                and obj_value is not None
            ):
                self.assertIsInstance(obj_value, obj_field.enum)

    def test_db_defaults_not_coerced(self):
        from django.db.models.expressions import DatabaseDefault

        empty_inst = DBDefaultTester()

        # check that the database default value fields are not coerced
        for field in [
            field for field in self.defaults.keys() if not field.startswith("doubled")
        ]:
            self.assertIsInstance(getattr(empty_inst, field), DatabaseDefault)
