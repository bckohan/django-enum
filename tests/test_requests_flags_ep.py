import pytest

pytest.importorskip("enum_properties")
from importlib.util import find_spec
from tests.test_requests_flags import TestFlagRequests
from tests.enum_prop.models import FlagFilterTester
from django.urls import reverse


class TestFlagRequestsProps(TestFlagRequests):
    MODEL_CLASS = FlagFilterTester
    NAMESPACE = "tests_enum_prop"

    @property
    def post_params(self):
        return {
            "small_flag": self.SmallPositiveFlagEnum.TWO
            | self.SmallPositiveFlagEnum.THREE,
            "flag": [self.PositiveFlagEnum.ONE.value | self.PositiveFlagEnum.TWO.value],
            "flag_no_coerce": 0,
            "big_flag": self.BigPositiveFlagEnum.ONE | (1 << 12) | (1 << 4),
        }

    @property
    def post_params_symmetric(self):
        return {
            "small_flag": self.SmallPositiveFlagEnum.TWO.number,
            "flag": [self.PositiveFlagEnum.ONE.name, self.PositiveFlagEnum.TWO.label],
            "flag_no_coerce": self.PositiveFlagEnum(0),
            "big_flag": [self.BigPositiveFlagEnum.ONE.version, (1 << 12), (1 << 4)],
        }

    @property
    def field_filter_properties(self):
        return {
            "small_flag": ["value", "name", "label", "number"],
            "flag": ["value", "name", "label", "number"],
            "flag_no_coerce": ["value", "name", "label", "number"],
            "big_flag": ["value", "name", "label", "version"],
        }

    def get_enum_val(self, enum, value):
        if value == "":
            return None
        return enum(value)

    if find_spec("rest_framework"):  # pragma: no cover

        def test_drf_flag_field(self):
            from django_enum.drf import FlagField

            super().test_drf_flag_field()

            field = FlagField(self.SmallPositiveFlagEnum)
            self.assertEqual(
                field.to_internal_value(
                    [
                        self.SmallPositiveFlagEnum.ONE.label,
                        self.SmallPositiveFlagEnum.TWO.number,
                    ]
                ),
                (self.SmallPositiveFlagEnum.ONE | self.SmallPositiveFlagEnum.TWO),
            )

    if find_spec("django_filters"):

        def test_django_filter_flags(self):
            self.do_test_django_filter(
                reverse(f"{self.NAMESPACE}:flag-filter-symmetric")
            )

        def test_django_filter_flags_exclude(self):
            self.do_test_django_filter(
                reverse(f"{self.NAMESPACE}:flag-filter-exclude-symmetric"), exclude=True
            )

        def test_django_filter_flags_conjoined(self):
            self.do_test_django_filter(
                reverse(f"{self.NAMESPACE}:flag-filter-conjoined-symmetric"),
                conjoined=True,
            )

        def test_django_filter_flags_conjoined_exclude(self):
            self.do_test_django_filter(
                reverse(f"{self.NAMESPACE}:flag-filter-conjoined-exclude-symmetric"),
                exclude=True,
                conjoined=True,
            )


# don't run these tests again!
TestFlagRequests = None
