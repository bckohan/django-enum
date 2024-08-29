import pytest

pytest.importorskip("enum_properties")

from tests.test_admin import TestAdmin
from tests.enum_prop.models import AdminDisplayBug35

class TestEnumPropAdmin(TestAdmin):

    BUG35_CLASS = AdminDisplayBug35

TestAdmin = None
