import pytest

pytest.importorskip("enum_properties")

from tests.test_bulk import TestBulkOperations
from tests.enum_prop.models import EnumTester


class TestBulkOperationsProps(TestBulkOperations):
    MODEL_CLASS = EnumTester

    @property
    def create_params(self):
        return {
            "small_pos_int": self.SmallPosIntEnum.VAL2,
            "small_int": "Value -32768",
            "pos_int": 2147483647,
            "int": -2147483648,
            "big_pos_int": "Value 2147483648",
            "big_int": "VAL2",
            "constant": "φ",
            "text": "V TWo",
            "extern": "One",
            "dj_int_enum": 3,
            "dj_text_enum": self.DJTextEnum.A,
            "non_strict_int": 15,
            "non_strict_text": "arbitrary",
            "no_coerce": "Value 2",
        }

    @property
    def update_params(self):
        return {
            "non_strict_int": 100,
            "non_strict_text": self.TextEnum.VALUE3,
            "constant": "π",
            "big_int": -2147483649,
            "coerce": 2,
        }


TestBulkOperations = None
