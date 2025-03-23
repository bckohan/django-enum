import typing as t
from enum import Enum
import pytest

pytest.importorskip("enum_properties")

from tests.test_admin import TestAdmin, TestEnumTesterAdminForm, _GenericAdminFormTest
from tests.enum_prop.models import AdminDisplayBug35, EnumTester, BitFieldModel
from tests.enum_prop.enums import (
    GNSSConstellation,
    LargeBitField,
    LargeNegativeField,
    LargeBitField,
)


class TestEnumPropAdmin(TestAdmin):
    BUG35_CLASS = AdminDisplayBug35


class TestEnumTesterPropsAdminForm(TestEnumTesterAdminForm):
    MODEL_CLASS = EnumTester
    __test__ = True


class TestBitFieldAdminForm(_GenericAdminFormTest):
    MODEL_CLASS = BitFieldModel
    HEADLESS = True
    __test__ = True

    @property
    def changes(self) -> t.List[t.Dict[str, t.Any]]:
        return [
            {
                "bit_field_small": GNSSConstellation.GLONASS | GNSSConstellation.GPS,
                "no_default": LargeBitField.ONE | LargeBitField.TWO,
            },
            {
                "bit_field_small": GNSSConstellation.GLONASS,
                "bit_field_large": LargeBitField.TWO | LargeBitField.ONE,
                "bit_field_large_empty_default": LargeBitField.TWO,
                "no_default": LargeBitField.TWO,
            },
            {
                "bit_field_small": GNSSConstellation(0),
                "bit_field_large": None,
                "bit_field_large_empty_default": LargeBitField(0),
                "no_default": LargeBitField(0),
            },
        ]


TestAdmin = None
TestEnumTesterAdminForm = None
