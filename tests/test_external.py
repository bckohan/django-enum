import enum
from django.test import TestCase
from django_enum.utils import choices, names, values, labels
from django.utils.functional import classproperty


class TestEnumCompat(TestCase):
    """Test that django_enum allows non-choice derived enums to be used"""

    from django.db.models import IntegerChoices as DJIntegerChoices

    class NormalIntEnum(enum.IntEnum):
        VAL1 = 1
        VAL2 = 2

    class IntEnumWithLabels(enum.IntEnum):
        __empty__ = 0

        VAL1 = 1
        VAL2 = 2

        @property
        def label(self):
            return {
                self.VAL1: "Label 1",
                self.VAL2: "Label 2",
            }.get(self)

    class ChoicesIntEnum(DJIntegerChoices):
        __empty__ = 0

        VAL1 = 1, "Label 1"
        VAL2 = 2, "Label 2"

    class EnumWithChoicesProperty(enum.Enum):
        VAL1 = 1
        VAL2 = 2

        @classproperty
        def choices(self):
            return [(self.VAL1.value, "Label 1"), (self.VAL2.value, "Label 2")]

    def test_choices(self):
        self.assertEqual(
            choices(TestEnumCompat.NormalIntEnum), [(1, "VAL1"), (2, "VAL2")]
        )
        self.assertEqual(
            choices(TestEnumCompat.IntEnumWithLabels),
            TestEnumCompat.ChoicesIntEnum.choices,
        )
        self.assertEqual(
            choices(TestEnumCompat.EnumWithChoicesProperty),
            [(1, "Label 1"), (2, "Label 2")],
        )
        self.assertEqual(choices(None), [])

    def test_labels(self):
        self.assertEqual(labels(TestEnumCompat.NormalIntEnum), ["VAL1", "VAL2"])
        self.assertEqual(
            labels(TestEnumCompat.IntEnumWithLabels),
            TestEnumCompat.ChoicesIntEnum.labels,
        )
        self.assertEqual(
            labels(TestEnumCompat.EnumWithChoicesProperty), ["Label 1", "Label 2"]
        )
        self.assertEqual(labels(None), [])

    def test_values(self):
        self.assertEqual(values(TestEnumCompat.NormalIntEnum), [1, 2])
        self.assertEqual(
            values(TestEnumCompat.IntEnumWithLabels),
            TestEnumCompat.ChoicesIntEnum.values,
        )
        self.assertEqual(values(TestEnumCompat.EnumWithChoicesProperty), [1, 2])
        self.assertEqual(values(None), [])

    def test_names(self):
        self.assertEqual(names(TestEnumCompat.NormalIntEnum), ["VAL1", "VAL2"])
        self.assertEqual(
            names(TestEnumCompat.IntEnumWithLabels), TestEnumCompat.ChoicesIntEnum.names
        )
        self.assertEqual(
            names(TestEnumCompat.EnumWithChoicesProperty), ["VAL1", "VAL2"]
        )
        self.assertEqual(names(None), [])
