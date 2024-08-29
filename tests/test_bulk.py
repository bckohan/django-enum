from django.test import TestCase
from tests.utils import EnumTypeMixin, IGNORE_ORA_01843
from tests.djenum.models import EnumTester
from django.db import connection
from django.db.utils import DatabaseError
import pytest


class TestBulkOperations(EnumTypeMixin, TestCase):
    """Tests bulk insertions and updates"""

    MODEL_CLASS = EnumTester
    NUMBER = 250

    def setUp(self):
        self.MODEL_CLASS.objects.all().delete()

    @property
    def create_params(self):
        return {
            "small_pos_int": self.SmallPosIntEnum.VAL2,
            "small_int": self.SmallIntEnum.VALn1,
            "pos_int": 2147483647,
            "int": -2147483648,
            "big_pos_int": self.BigPosIntEnum.VAL3,
            "big_int": self.BigIntEnum.VAL2,
            "constant": self.Constants.GOLDEN_RATIO,
            "text": self.TextEnum.VALUE2,
            "extern": self.ExternEnum.TWO,
            "date_enum": self.DateEnum.HUGO,
            "datetime_enum": self.DateTimeEnum.KATRINA,
            "time_enum": self.TimeEnum.COB,
            "duration_enum": self.DurationEnum.FORTNIGHT,
            "decimal_enum": self.DecimalEnum.FIVE,
            "dj_int_enum": 3,
            "dj_text_enum": self.DJTextEnum.A,
            "non_strict_int": 15,
            "non_strict_text": "arbitrary",
            "no_coerce": "0",
        }

    @property
    def update_params(self):
        return {
            "non_strict_int": 100,
            "constant": self.Constants.PI,
            "big_int": -2147483649,
            "date_enum": self.DateEnum.BRIAN,
            "datetime_enum": self.DateTimeEnum.ST_HELENS,
            "time_enum": self.TimeEnum.LUNCH,
            "duration_enum": self.DurationEnum.WEEK,
            "decimal_enum": self.DecimalEnum.TWO,
        }

    def test_bulk_create(self):
        try:
            objects = []
            for _ in range(0, self.NUMBER):
                objects.append(self.MODEL_CLASS(**self.create_params))

            self.MODEL_CLASS.objects.bulk_create(objects)

            self.assertEqual(
                self.MODEL_CLASS.objects.filter(**self.create_params).count(),
                self.NUMBER,
            )
        except DatabaseError as err:
            print(str(err))
            if (
                IGNORE_ORA_01843
                and connection.vendor == "oracle"
                and "ORA-01843" in str(err)
            ):
                # this is an oracle bug - intermittent failure on
                # perfectly fine date format in SQL
                # continue
                pytest.skip("Oracle bug ORA-01843 encountered - skipping")
            raise

    def test_bulk_update(self):
        try:
            objects = []
            for obj in range(0, self.NUMBER):
                obj = self.MODEL_CLASS.objects.create(**self.create_params)
                for param, value in self.update_params.items():
                    setattr(obj, param, value)
                objects.append(obj)

            self.assertEqual(len(objects), self.NUMBER)
            to_update = ["constant", "non_strict_int"]
            self.MODEL_CLASS.objects.bulk_update(objects, to_update)

            self.assertEqual(
                self.MODEL_CLASS.objects.filter(
                    **{
                        **self.create_params,
                        **{
                            param: val
                            for param, val in self.update_params.items()
                            if param in to_update
                        },
                    }
                ).count(),
                self.NUMBER,
            )
        except DatabaseError as err:
            print(str(err))
            if (
                IGNORE_ORA_01843
                and connection.vendor == "oracle"
                and "ORA-01843" in str(err)
            ):
                # this is an oracle bug - intermittent failure on
                # perfectly fine date format in SQL
                # continue
                pytest.skip("Oracle bug ORA-01843 encountered - skipping")
            raise
