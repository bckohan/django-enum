import pytest

pytest.importorskip("enum_properties")
from tests.test_forms import FormTests, TestFormField
from tests.enum_prop.models import EnumTester
from tests.enum_prop.forms import EnumTesterForm


class EnumPropertiesFormTests(FormTests):
    MODEL_CLASS = EnumTester


class TestFormFieldSymmetric(TestFormField):
    MODEL_CLASS = EnumTester
    FORM_CLASS = EnumTesterForm
    form_type = None

    @property
    def model_params(self):
        return {
            "small_pos_int": 0,
            "small_int": self.SmallIntEnum.VAL2,
            "pos_int": "Value 2147483647",
            "int": "VALn1",
            "big_pos_int": 2,
            "big_int": self.BigPosIntEnum.VAL2,
            "constant": "π",
            "text": "none",
            "extern": "three",
            "dj_int_enum": 2,
            "dj_text_enum": "B",
            "non_strict_int": 1,
            "non_strict_text": "arbitrary",
            "no_coerce": "Value 1",
        }


FormTests = None
TestFormField = None
