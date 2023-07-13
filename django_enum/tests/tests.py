import enum
import os
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from bs4 import BeautifulSoup as Soup
from django.core import serializers
from django.core.exceptions import FieldError, ValidationError
from django.core.management import call_command
from django.db import connection, transaction
from django.db.models import F, Q
from django.http import QueryDict
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.functional import classproperty
from django_enum import EnumField, TextChoices
from django_enum.fields import (
    BigIntegerFlagField,
    EnumExtraBigIntegerField,
    ExtraBigIntegerFlagField,
    FlagField,
    IntegerFlagField,
    SmallIntegerFlagField,
)
from django_enum.forms import EnumChoiceField  # dont remove this
# from django_enum.tests.djenum.enums import (
#     BigIntEnum,
#     BigPosIntEnum,
#     Constants,
#     DJIntEnum,
#     DJTextEnum,
#     IntEnum,
#     PosIntEnum,
#     SmallIntEnum,
#     SmallPosIntEnum,
#     TextEnum,
#     ExternEnum
# )
from django_enum.tests.djenum.forms import EnumTesterForm
from django_enum.tests.djenum.models import (
    BadDefault,
    EnumFlagTester,
    EnumTester,
)
from django_enum.tests.utils import try_convert
from django_enum.utils import choices, labels, names, values
from django_test_migrations.constants import MIGRATION_TEST_MARKER
from django_test_migrations.contrib.unittest_case import MigratorTestCase

try:
    import django_filters
    DJANGO_FILTERS_INSTALLED = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    DJANGO_FILTERS_INSTALLED = False

try:
    import rest_framework
    DJANGO_RESTFRAMEWORK_INSTALLED = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    DJANGO_RESTFRAMEWORK_INSTALLED = False

try:
    import enum_properties
    ENUM_PROPERTIES_INSTALLED = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    ENUM_PROPERTIES_INSTALLED = False


# MySQL <8 does not support check constraints which is a problem for the
# migration tests - we have this check here to allow CI to disable them and
# still run the rest of the tests on mysql versions < 8 - remove this when
# 8 becomes the lowest version Django supports
DISABLE_MIGRATION_TESTS = (
    os.environ.get('MYSQL_VERSION', '') == '5.7'
)


def combine_flags(*flags):
    if flags:
        flag = flags[0]
        for flg in flags[1:]:
            flag = flag | flg
        return flag
    return 0


def invert_flags(en):
    # invert a flag enumeration. in python 3.11+ ~ operator is supported
    if sys.version_info >= (3, 11, 4) and en.value > 0:
        return ~en
    return en.__class__(
        combine_flags(*[
            flag for flag in list(en.__class__.__members__.values())
            if flag not in en
        ])
    )


def set_models(version):
    import warnings
    from importlib import reload
    from shutil import copyfile

    from django.conf import settings

    from .edit_tests import models

    copyfile(
        settings.TEST_EDIT_DIR / f'_{version}.py',
        settings.TEST_MIGRATION_DIR.parent / 'models.py'
    )

    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        reload(models)


APP1_DIR = Path(__file__).parent / 'enum_prop'


class EnumTypeMixin:
    """
    We make use of inheritance to re-run lots of tests with vanilla Django choices
    enumerations and enumerations defined with integration with enum-properties.

    Since most of this code is identical, we use this mixin to resolve the correct
    type at the specific test in question.
    """

    fields = [
        'small_pos_int',
        'small_int',
        'pos_int',
        'int',
        'big_pos_int',
        'big_int',
        'constant',
        'text',
        'extern',
        'date_enum',
        'datetime_enum',
        'duration_enum',
        'time_enum',
        'decimal_enum',
        'dj_int_enum',
        'dj_text_enum',
        'non_strict_int',
        'non_strict_text',
        'no_coerce',
    ]

    @property
    def SmallPosIntEnum(self):
        return self.MODEL_CLASS._meta.get_field('small_pos_int').enum

    @property
    def SmallIntEnum(self):
        return self.MODEL_CLASS._meta.get_field('small_int').enum

    @property
    def PosIntEnum(self):
        return self.MODEL_CLASS._meta.get_field('pos_int').enum

    @property
    def IntEnum(self):
        return self.MODEL_CLASS._meta.get_field('int').enum

    @property
    def BigPosIntEnum(self):
        return self.MODEL_CLASS._meta.get_field('big_pos_int').enum

    @property
    def BigIntEnum(self):
        return self.MODEL_CLASS._meta.get_field('big_int').enum

    @property
    def Constants(self):
        return self.MODEL_CLASS._meta.get_field('constant').enum

    @property
    def TextEnum(self):
        return self.MODEL_CLASS._meta.get_field('text').enum

    @property
    def ExternEnum(self):
        return self.MODEL_CLASS._meta.get_field('extern').enum

    @property
    def DJIntEnum(self):
        return self.MODEL_CLASS._meta.get_field('dj_int_enum').enum

    @property
    def DJTextEnum(self):
        return self.MODEL_CLASS._meta.get_field('dj_text_enum').enum

    def enum_type(self, field_name):
        return self.MODEL_CLASS._meta.get_field(field_name).enum

    @property
    def DateEnum(self):
        return self.MODEL_CLASS._meta.get_field('date_enum').enum

    @property
    def DateTimeEnum(self):
        return self.MODEL_CLASS._meta.get_field('datetime_enum').enum

    @property
    def DurationEnum(self):
        return self.MODEL_CLASS._meta.get_field('duration_enum').enum

    @property
    def TimeEnum(self):
        return self.MODEL_CLASS._meta.get_field('time_enum').enum

    @property
    def DecimalEnum(self):
        return self.MODEL_CLASS._meta.get_field('decimal_enum').enum

    def enum_primitive(self, field_name):
        enum_type = self.enum_type(field_name)
        if enum_type in {
            self.SmallPosIntEnum, self.SmallIntEnum, self.IntEnum,
            self.PosIntEnum, self.BigIntEnum, self.BigPosIntEnum,
            self.DJIntEnum, self.ExternEnum
        }:
            return int
        elif enum_type is self.Constants:
            return float
        elif enum_type in {self.TextEnum, self.DJTextEnum}:
            return str
        elif enum_type is self.DateEnum:
            return date
        elif enum_type is self.DateTimeEnum:
            return datetime
        elif enum_type is self.DurationEnum:
            return timedelta
        elif enum_type is self.TimeEnum:
            return time
        elif enum_type is self.DecimalEnum:
            return Decimal
        else:  # pragma: no cover
            raise RuntimeError(f'Missing enum type primitive for {enum_type}')


class TestValidatorAdapter(TestCase):

    def test(self):
        from django.core.validators import DecimalValidator
        from django_enum.fields import EnumValidatorAdapter
        validator = DecimalValidator(max_digits=5, decimal_places=2)
        adapted = EnumValidatorAdapter(validator)
        self.assertEqual(adapted.max_digits, validator.max_digits)
        self.assertEqual(adapted.decimal_places, validator.decimal_places)
        self.assertEqual(adapted, validator)
        self.assertEqual(repr(adapted), f'EnumValidatorAdapter({repr(validator)})')
        ok = Decimal('123.45')
        bad = Decimal('123.456')
        self.assertIsNone(validator(ok))
        self.assertIsNone(adapted(ok))
        self.assertRaises(ValidationError, validator, bad)
        self.assertRaises(ValidationError, adapted, bad)


class TestEccentricEnums(TestCase):

    def test_primitive_resolution(self):
        from django_enum.tests.djenum.models import MultiPrimitiveTestModel
        self.assertEqual(
            MultiPrimitiveTestModel._meta.get_field('multi').primitive,
            str
        )
        self.assertEqual(
            MultiPrimitiveTestModel._meta.get_field('multi_float').primitive,
            float
        )
        self.assertEqual(
            MultiPrimitiveTestModel._meta.get_field('multi_none').primitive,
            str
        )

    def test_multiple_primitives(self):
        from django_enum.tests.djenum.models import (
            MultiPrimitiveEnum,
            MultiPrimitiveTestModel,
            MultiWithNone,
        )
        empty = MultiPrimitiveTestModel.objects.create()
        obj1 = MultiPrimitiveTestModel.objects.create(
            multi=MultiPrimitiveEnum.VAL1
        )
        obj2 = MultiPrimitiveTestModel.objects.create(
            multi=MultiPrimitiveEnum.VAL2
        )
        obj3 = MultiPrimitiveTestModel.objects.create(
            multi=MultiPrimitiveEnum.VAL3
        )
        obj4 = MultiPrimitiveTestModel.objects.create(
            multi=MultiPrimitiveEnum.VAL4
        )

        srch0 = MultiPrimitiveTestModel.objects.filter(multi__isnull=True)
        srch1 = MultiPrimitiveTestModel.objects.filter(multi=MultiPrimitiveEnum.VAL1)
        srch2 = MultiPrimitiveTestModel.objects.filter(multi=MultiPrimitiveEnum.VAL2)
        srch3 = MultiPrimitiveTestModel.objects.filter(multi=MultiPrimitiveEnum.VAL3)
        srch4 = MultiPrimitiveTestModel.objects.filter(multi=MultiPrimitiveEnum.VAL4)
        srch_p1 = MultiPrimitiveTestModel.objects.filter(multi=1)
        srch_p2 = MultiPrimitiveTestModel.objects.filter(multi='2.0')
        srch_p3 = MultiPrimitiveTestModel.objects.filter(multi=3.0)
        srch_p4 = MultiPrimitiveTestModel.objects.filter(multi=Decimal('4.5'))

        with self.assertRaises(ValueError):
            MultiPrimitiveTestModel.objects.filter(multi='1')

        with self.assertRaises(ValueError):
            MultiPrimitiveTestModel.objects.filter(multi='3.0')

        with self.assertRaises(ValueError):
            MultiPrimitiveTestModel.objects.filter(multi='4.5')

        self.assertEqual(srch0.count(), 1)
        self.assertEqual(srch1.count(), 1)
        self.assertEqual(srch2.count(), 1)
        self.assertEqual(srch3.count(), 1)
        self.assertEqual(srch4.count(), 1)
        self.assertEqual(srch_p1.count(), 1)
        self.assertEqual(srch_p2.count(), 1)
        self.assertEqual(srch_p3.count(), 1)
        self.assertEqual(srch_p4.count(), 1)

        self.assertEqual(srch0[0], empty)
        self.assertEqual(srch1[0], obj1)
        self.assertEqual(srch2[0], obj2)
        self.assertEqual(srch3[0], obj3)
        self.assertEqual(srch4[0], obj4)
        self.assertEqual(srch_p1[0], obj1)
        self.assertEqual(srch_p2[0], obj2)
        self.assertEqual(srch_p3[0], obj3)
        self.assertEqual(srch_p4[0], obj4)

        self.assertEqual(
            MultiPrimitiveTestModel.objects.filter(
                multi_float=MultiPrimitiveEnum.VAL2
            ).count(), 5
        )

        obj5 = MultiPrimitiveTestModel.objects.create(
            multi_none=None
        )

        nq0 = MultiPrimitiveTestModel.objects.filter(
            multi_none=MultiWithNone.NONE
        )
        nq1 = MultiPrimitiveTestModel.objects.filter(
            multi_none__isnull=True
        )
        nq2 = MultiPrimitiveTestModel.objects.filter(
            multi_none=None
        )
        self.assertEqual(nq0.count(), 1)
        self.assertEqual(nq1.count(), 1)
        self.assertEqual(nq2.count(), 1)
        self.assertTrue(nq0[0] == nq1[0] == nq2[0] == obj5)

    def test_enum_choice_field(self):
        from django_enum.tests.djenum.enums import (
            MultiPrimitiveEnum,
            MultiWithNone,
        )

        form_field1 = EnumChoiceField(MultiPrimitiveEnum)
        self.assertEqual(form_field1.choices, choices(MultiPrimitiveEnum))
        self.assertEqual(form_field1.primitive, str)

        form_field2 = EnumChoiceField(MultiPrimitiveEnum, primitive=float)
        self.assertEqual(form_field2.choices, choices(MultiPrimitiveEnum))
        self.assertEqual(form_field2.primitive, float)

        form_field3 = EnumChoiceField(MultiWithNone)
        self.assertEqual(form_field3.choices, choices(MultiWithNone))
        self.assertEqual(form_field3.primitive, str)


class TestEnumCompat(TestCase):
    """ Test that django_enum allows non-choice derived enums to be used """

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
                self.VAL1: 'Label 1',
                self.VAL2: 'Label 2',
            }.get(self)

    class ChoicesIntEnum(DJIntegerChoices):

        __empty__ = 0

        VAL1 = 1, 'Label 1'
        VAL2 = 2, 'Label 2'

    class EnumWithChoicesProperty(enum.Enum):
        VAL1 = 1
        VAL2 = 2

        @classproperty
        def choices(self):
            return [(self.VAL1.value, 'Label 1'), (self.VAL2.value, 'Label 2')]

    def test_choices(self):

        self.assertEqual(
            choices(TestEnumCompat.NormalIntEnum),
            [(1, 'VAL1'), (2, 'VAL2')]
        )
        self.assertEqual(
            choices(TestEnumCompat.IntEnumWithLabels),
            TestEnumCompat.ChoicesIntEnum.choices
        )
        self.assertEqual(
            choices(TestEnumCompat.EnumWithChoicesProperty),
            [(1, 'Label 1'), (2, 'Label 2')]
        )
        self.assertEqual(
            choices(None),
            []
        )

    def test_labels(self):
        self.assertEqual(
            labels(TestEnumCompat.NormalIntEnum),
            ['VAL1', 'VAL2']
        )
        self.assertEqual(
            labels(TestEnumCompat.IntEnumWithLabels),
            TestEnumCompat.ChoicesIntEnum.labels
        )
        self.assertEqual(
            labels(TestEnumCompat.EnumWithChoicesProperty),
            ['Label 1', 'Label 2']
        )
        self.assertEqual(
            labels(None),
            []
        )

    def test_values(self):
        self.assertEqual(
            values(TestEnumCompat.NormalIntEnum),
            [1, 2]
        )
        self.assertEqual(
            values(TestEnumCompat.IntEnumWithLabels),
            TestEnumCompat.ChoicesIntEnum.values
        )
        self.assertEqual(
            values(TestEnumCompat.EnumWithChoicesProperty),
            [1, 2]
        )
        self.assertEqual(
            values(None),
            []
        )

    def test_names(self):
        self.assertEqual(
            names(TestEnumCompat.NormalIntEnum),
            ['VAL1', 'VAL2']
        )
        self.assertEqual(
            names(TestEnumCompat.IntEnumWithLabels),
            TestEnumCompat.ChoicesIntEnum.names
        )
        self.assertEqual(
            names(TestEnumCompat.EnumWithChoicesProperty),
            ['VAL1', 'VAL2']
        )
        self.assertEqual(
            names(None),
            []
        )


class TestChoices(EnumTypeMixin, TestCase):
    """Test that Django's choices types work as expected"""

    MODEL_CLASS = EnumTester

    def setUp(self):
        self.MODEL_CLASS.objects.all().delete()

    @property
    def create_params(self):
        return {
            'small_pos_int': self.SmallPosIntEnum.VAL2,
            'small_int': self.SmallIntEnum.VALn1,
            'pos_int': 2147483647,
            'int': -2147483648,
            'big_pos_int': self.BigPosIntEnum.VAL3,
            'big_int': self.BigIntEnum.VAL2,
            'constant': self.Constants.GOLDEN_RATIO,
            'text': self.TextEnum.VALUE2,
            'extern': self.ExternEnum.THREE,
            'date_enum': self.DateEnum.HUGO,
            'datetime_enum': self.DateTimeEnum.PINATUBO,
            'duration_enum': self.DurationEnum.DAY,
            'time_enum': self.TimeEnum.LUNCH,
            'decimal_enum': self.DecimalEnum.FOUR
        }

    def test_defaults(self):
        from django.db.models import NOT_PROVIDED

        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('small_pos_int').get_default(),
            None
        )

        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('small_int').get_default(),
            self.enum_type('small_int').VAL3
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field('small_int').get_default(),
            self.enum_type('small_int')
        )

        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('pos_int').get_default(),
            self.enum_type('pos_int').VAL3
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field('pos_int').get_default(),
            self.enum_type('pos_int')
        )

        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('int').get_default(),
            None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('big_pos_int').get_default(),
            None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('big_int').get_default(),
            self.enum_type('big_int').VAL0
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field('big_int').get_default(),
            self.enum_type('big_int')
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('constant').get_default(),
            None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('text').get_default(),
            None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('extern').get_default(),
            None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('date_enum').get_default(),
            self.enum_type('date_enum').EMMA
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('datetime_enum').get_default(),
            None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('duration_enum').get_default(),
            None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('time_enum').get_default(),
            None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('decimal_enum').get_default(),
            self.enum_type('decimal_enum').THREE
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('dj_int_enum').get_default(),
            self.enum_type('dj_int_enum').ONE
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field('dj_int_enum').get_default(),
            self.enum_type('dj_int_enum')
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('dj_text_enum').get_default(),
            self.enum_type('dj_text_enum').A
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field('dj_text_enum').get_default(),
            self.enum_type('dj_text_enum')
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('non_strict_int').get_default(),
            5
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field('non_strict_int').get_default(),
            self.enum_primitive('non_strict_int')
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('non_strict_text').get_default(),
            ''
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field('no_coerce').get_default(),
            None
        )

        self.assertEqual(
            BadDefault._meta.get_field('non_strict_int').get_default(),
            5
        )

        self.assertRaises(
            ValueError,
            BadDefault.objects.create
        )

    def test_basic_save(self):
        self.MODEL_CLASS.objects.all().delete()
        self.MODEL_CLASS.objects.create(**self.create_params)
        for param in self.fields:
            value = self.create_params.get(
                param,
                self.MODEL_CLASS._meta.get_field(param).get_default()
            )
            self.assertEqual(
                self.MODEL_CLASS.objects.filter(**{param: value}).count(),
                1
            )
        self.MODEL_CLASS.objects.all().delete()

    def test_to_python_deferred_attribute(self):
        obj = self.MODEL_CLASS.objects.create(**self.create_params)
        with self.assertNumQueries(1):
            obj2 = self.MODEL_CLASS.objects.only('id').get(pk=obj.pk)

        for field in [
            field.name for field in self.MODEL_CLASS._meta.fields
            if field.name != 'id'
        ]:
            # each of these should result in a db query
            with self.assertNumQueries(1):
                self.assertEqual(
                    getattr(obj, field),
                    getattr(obj2, field)
                )

            with self.assertNumQueries(2):
                self.assertEqual(
                    getattr(
                        self.MODEL_CLASS.objects.defer(field).get(pk=obj.pk),
                        field
                    ),
                    getattr(obj, field),
                )

        # test that all coerced fields are coerced to the Enum type on
        # assignment - this also tests symmetric value assignment in the
        # derived class
        set_tester = self.MODEL_CLASS()
        for field, value in self.values_params.items():
            setattr(set_tester, field, getattr(value, 'value', value))
            if self.MODEL_CLASS._meta.get_field(field).coerce:
                try:
                    self.assertIsInstance(getattr(set_tester, field), self.enum_type(field))
                except AssertionError:
                    self.assertFalse(self.MODEL_CLASS._meta.get_field(field).strict)
                    self.assertIsInstance(getattr(set_tester, field), self.enum_primitive(field))
            else:
                self.assertNotIsInstance(getattr(set_tester, field), self.enum_type(field))
                self.assertIsInstance(getattr(set_tester, field), self.enum_primitive(field))

        # extra verification - save and make sure values are expected
        set_tester.save()
        set_tester.refresh_from_db()
        for field, value in self.values_params.items():
            self.assertEqual(getattr(set_tester, field), value)

    def test_integer_choices(self):
        self.do_test_integer_choices()

    def do_test_integer_choices(self):

        self.MODEL_CLASS.objects.create(dj_int_enum=self.DJIntEnum.ONE)
        self.MODEL_CLASS.objects.create(dj_int_enum=self.DJIntEnum.TWO)
        self.MODEL_CLASS.objects.create(dj_int_enum=self.DJIntEnum.THREE)

        for obj in self.MODEL_CLASS.objects.all():
            self.assertIsInstance(obj.dj_int_enum, self.DJIntEnum)

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum='1').count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=1).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum.ONE).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum(1)).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum['ONE']).count(), 1)

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum='2').count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=2).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum.TWO).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum(2)).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum['TWO']).count(), 1)

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum='3').count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=3).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum.THREE).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum(3)).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum['THREE']).count(), 1)

    def test_text_choices(self):
        self.do_test_text_choices()

    def do_test_text_choices(self):
        self.MODEL_CLASS.objects.all().delete()
        self.MODEL_CLASS.objects.create(dj_text_enum=self.DJTextEnum.A)
        self.MODEL_CLASS.objects.create(dj_text_enum=self.DJTextEnum.B)
        self.MODEL_CLASS.objects.create(dj_text_enum=self.DJTextEnum.C)

        for obj in self.MODEL_CLASS.objects.all():
            self.assertIsInstance(obj.dj_text_enum, self.DJTextEnum)

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum='A').count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum.A).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum('A')).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum['A']).count(), 1)

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum='B').count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum.B).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum('B')).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum['B']).count(), 1)

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum='C').count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum.C).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum('C')).count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum['C']).count(), 1)

    @property
    def values_params(self):
        return {
            'small_pos_int': self.SmallPosIntEnum.VAL2,
            'small_int': self.SmallIntEnum.VALn1,
            'pos_int': self.PosIntEnum.VAL3,
            'int': self.IntEnum.VALn1,
            'big_pos_int': self.BigPosIntEnum.VAL3,
            'big_int': self.BigIntEnum.VAL2,
            'constant': self.Constants.GOLDEN_RATIO,
            'text': self.TextEnum.VALUE2,
            'extern': self.ExternEnum.TWO,
            'dj_int_enum': 3,
            'dj_text_enum': self.DJTextEnum.A,
            'non_strict_int':  75,
            'non_strict_text':  'arbitrary',
            'no_coerce': self.SmallPosIntEnum.VAL2,
            'datetime_enum': self.DateTimeEnum.ST_HELENS,
            'duration_enum': self.DurationEnum.DAY,
            'time_enum': self.TimeEnum.MORNING
        }

    def do_test_values(self):
        """
        tests that queryset values returns Enumeration instances for enum
        fields
        """
        obj = self.MODEL_CLASS.objects.create(**self.values_params)

        values1 = self.MODEL_CLASS.objects.filter(pk=obj.pk).values().first()
        self.assertEqual(values1['small_pos_int'], self.SmallPosIntEnum.VAL2)
        self.assertEqual(values1['small_int'], self.SmallIntEnum.VALn1)
        self.assertEqual(values1['pos_int'], self.PosIntEnum.VAL3)
        self.assertEqual(values1['int'], self.IntEnum.VALn1)
        self.assertEqual(values1['big_pos_int'], self.BigPosIntEnum.VAL3)
        self.assertEqual(values1['big_int'], self.BigIntEnum.VAL2)
        self.assertEqual(values1['constant'], self.Constants.GOLDEN_RATIO)
        self.assertEqual(values1['text'], self.TextEnum.VALUE2)
        self.assertEqual(values1['extern'], self.ExternEnum.TWO)
        self.assertEqual(values1['dj_int_enum'], self.DJIntEnum.THREE)
        self.assertEqual(values1['dj_text_enum'], self.DJTextEnum.A)

        self.assertIsInstance(values1['small_pos_int'], self.SmallPosIntEnum)
        self.assertIsInstance(values1['small_int'], self.SmallIntEnum)
        self.assertIsInstance(values1['pos_int'], self.PosIntEnum)
        self.assertIsInstance(values1['int'], self.IntEnum)
        self.assertIsInstance(values1['big_pos_int'], self.BigPosIntEnum)
        self.assertIsInstance(values1['big_int'], self.BigIntEnum)
        self.assertIsInstance(values1['constant'], self.Constants)
        self.assertIsInstance(values1['text'], self.TextEnum)
        self.assertIsInstance(values1['dj_int_enum'], self.DJIntEnum)
        self.assertIsInstance(values1['dj_text_enum'], self.DJTextEnum)

        self.assertEqual(values1['non_strict_int'], 75)
        self.assertEqual(values1['non_strict_text'], 'arbitrary')
        self.assertEqual(values1['no_coerce'], 2)

        self.assertNotIsInstance(values1['non_strict_int'], self.SmallPosIntEnum)
        self.assertNotIsInstance(values1['non_strict_text'], self.TextEnum)
        self.assertNotIsInstance(values1['no_coerce'], self.SmallPosIntEnum)

        obj.delete()

        obj = self.MODEL_CLASS.objects.create(
            non_strict_int=self.SmallPosIntEnum.VAL1,
            non_strict_text=self.TextEnum.VALUE3,
            no_coerce=self.SmallPosIntEnum.VAL3
        )
        values2 = self.MODEL_CLASS.objects.filter(pk=obj.pk).values().first()
        self.assertEqual(values2['non_strict_int'], self.SmallPosIntEnum.VAL1)
        self.assertEqual(values2['non_strict_text'], self.TextEnum.VALUE3)
        self.assertEqual(values2['no_coerce'], self.SmallPosIntEnum.VAL3)
        self.assertIsInstance(values2['non_strict_int'], self.SmallPosIntEnum)
        self.assertIsInstance(values2['non_strict_text'], self.TextEnum)
        self.assertNotIsInstance(values2['no_coerce'], self.SmallPosIntEnum)

        self.assertEqual(values2['dj_int_enum'], 1)
        self.assertEqual(values2['dj_text_enum'], 'A')

        return values1, values2

    def test_values(self):
        self.do_test_values()

    def test_non_strict(self):
        """
        Test that non strict fields allow assignment and read of non-enum values.
        """
        values = {
            (self.SmallPosIntEnum.VAL1, self.TextEnum.VALUE1),
            (self.SmallPosIntEnum.VAL2, self.TextEnum.VALUE2),
            (self.SmallPosIntEnum.VAL3, self.TextEnum.VALUE3),
            (10, 'arb'),
            (12, 'arbitra'),
            (15, 'A'*12)
        }
        for int_val, txt_val in values:
            self.MODEL_CLASS.objects.create(
                non_strict_int=int_val,
                non_strict_text=txt_val
            )

        for obj in self.MODEL_CLASS.objects.filter(
                Q(non_strict_int__isnull=False) & Q(non_strict_text__isnull=False)
        ):
            self.assertTrue(obj.non_strict_int in [val[0] for val in values])
            self.assertTrue(obj.non_strict_text in [val[1] for val in values])

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=self.SmallPosIntEnum.VAL1,
                non_strict_text=self.TextEnum.VALUE1
            ).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=self.SmallPosIntEnum.VAL2,
                non_strict_text=self.TextEnum.VALUE2
            ).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=self.SmallPosIntEnum.VAL3,
                non_strict_text=self.TextEnum.VALUE3
            ).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=10,
                non_strict_text='arb'
            ).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=12,
                non_strict_text='arbitra'
            ).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=15,
                non_strict_text='A'*12
            ).count(), 1
        )

    def test_max_length_override(self):

        self.assertEqual(self.MODEL_CLASS._meta.get_field('non_strict_text').max_length, 12)
        # todo sqlite does not enforce the max_length of a VARCHAR, make this
        #   test specific to database backends that do
        # will raise in certain backends
        # obj = self.MODEL_CLASS.objects.create(
        #    non_strict_text='A'*13
        # )
        # print(len(obj.non_strict_text))

    def test_serialization(self):
        tester = self.MODEL_CLASS.objects.create(**self.values_params)
        from django.core.serializers import json
        serialized = serializers.serialize('json', self.MODEL_CLASS.objects.all())

        tester.delete()

        for mdl in serializers.deserialize('json', serialized):
            mdl.save()
            tester = mdl.object

        for param, value in self.values_params.items():
            self.assertEqual(getattr(tester, param), value)

    def do_test_validate(self):
        tester = self.MODEL_CLASS.objects.create()
        self.assertRaises(ValidationError, tester._meta.get_field('small_pos_int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('small_int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('pos_int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('big_pos_int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('big_int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('constant').validate, 66.6, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('text').validate, '666', tester)
        self.assertRaises(ValidationError, tester._meta.get_field('extern').validate, 6, tester)

        # coerce=False still validates
        self.assertRaises(ValidationError, tester._meta.get_field('no_coerce').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('no_coerce').validate, 'a', tester)

        # non strict fields whose type can't be coerced to the enum's primitive will fail to validate
        self.assertRaises(ValidationError, tester._meta.get_field('non_strict_int').validate, 'a', tester)

        self.assertRaises(ValidationError, tester._meta.get_field('small_pos_int').validate, 'anna', tester)
        self.assertRaises(ValidationError, tester._meta.get_field('small_int').validate, 'maria', tester)
        self.assertRaises(ValidationError, tester._meta.get_field('pos_int').validate, 'montes', tester)
        self.assertRaises(ValidationError, tester._meta.get_field('int').validate, '3<', tester)
        self.assertRaises(ValidationError, tester._meta.get_field('big_pos_int').validate, 'itwb', tester)
        self.assertRaises(ValidationError, tester._meta.get_field('big_int').validate, 'walwchh', tester)
        self.assertRaises(ValidationError, tester._meta.get_field('constant').validate, 'xx.x', tester)
        self.assertRaises(ValidationError, tester._meta.get_field('text').validate, '666', tester)

        self.assertRaises(ValidationError, tester._meta.get_field('small_int').validate, None, tester)

        self.assertTrue(tester._meta.get_field('small_pos_int').validate(0, tester) is None)
        self.assertTrue(tester._meta.get_field('small_int').validate(-32768, tester) is None)
        self.assertTrue(tester._meta.get_field('pos_int').validate(2147483647, tester) is None)
        self.assertTrue(tester._meta.get_field('int').validate(-2147483648, tester) is None)
        self.assertTrue(tester._meta.get_field('big_pos_int').validate(2147483648, tester) is None)
        self.assertTrue(tester._meta.get_field('big_int').validate(2, tester) is None)
        self.assertTrue(tester._meta.get_field('constant').validate(1.61803398874989484820458683436563811, tester) is None)
        self.assertTrue(tester._meta.get_field('text').validate('D', tester) is None)

        self.assertTrue(tester._meta.get_field('dj_int_enum').validate(1, tester) is None)
        self.assertTrue(tester._meta.get_field('dj_text_enum').validate('A', tester) is None)
        self.assertTrue(tester._meta.get_field('non_strict_int').validate(20, tester) is None)
        self.assertTrue(tester._meta.get_field('non_strict_text').validate('A'*12, tester) is None)

        return tester

    def test_validate(self):
        self.do_test_validate()

    def test_clean(self):

        tester = self.MODEL_CLASS(
            small_pos_int=666,
            small_int=666,
            pos_int=666,
            int=666,
            big_pos_int=666,
            big_int=666,
            constant=66.6,
            text='666',
            extern=6
        )
        try:
            tester.full_clean()
            self.assertTrue(False, "full_clean should have thrown a ValidationError")  # pragma: no cover
        except ValidationError as ve:
            self.assertTrue('small_pos_int' in ve.message_dict)
            self.assertTrue('small_int' in ve.message_dict)
            self.assertTrue('pos_int' in ve.message_dict)
            self.assertTrue('int' in ve.message_dict)
            self.assertTrue('big_pos_int' in ve.message_dict)
            self.assertTrue('big_int' in ve.message_dict)
            self.assertTrue('constant' in ve.message_dict)
            self.assertTrue('text' in ve.message_dict)
            self.assertTrue('extern' in ve.message_dict)

    def do_rest_framework_missing(self):
        from django_enum.drf import EnumField
        self.assertRaises(ImportError, EnumField, self.SmallPosIntEnum)

    def test_rest_framework_missing(self):
        import sys
        from importlib import reload
        from unittest.mock import patch

        from django_enum import drf
        if 'rest_framework.fields' in sys.modules:
            with patch.dict(sys.modules, {'rest_framework.fields': None}):
                reload(sys.modules['django_enum.drf'])
                self.do_rest_framework_missing()
            reload(sys.modules['django_enum.drf'])
        else:
            self.do_rest_framework_missing()  # pragma: no cover

    def do_django_filters_missing(self):
        from django_enum.filters import EnumFilter
        from django_enum.filters import FilterSet as EnumFilterSet

        class EnumTesterFilter(EnumFilterSet):
            class Meta:
                model = EnumTester
                fields = '__all__'

        self.assertRaises(ImportError, EnumTesterFilter)
        self.assertRaises(ImportError, EnumFilter)

    def test_django_filters_missing(self):
        import sys
        from importlib import reload
        from unittest.mock import patch

        from django_enum import filters

        if 'django_filters' in sys.modules:
            with patch.dict(sys.modules, {'django_filters': None}):
                reload(sys.modules['django_enum.filters'])
                self.do_django_filters_missing()
            reload(sys.modules['django_enum.filters'])
        else:
            self.do_django_filters_missing()  # pragma: no cover

    def do_enum_properties_missing(self):
        import enum

        from django_enum.choices import (
            DjangoEnumPropertiesMeta,
            DjangoSymmetricMixin,
            FloatChoices,
            IntegerChoices,
            TextChoices,
        )

        with self.assertRaises(ImportError):
            class ThrowsEnum(DjangoSymmetricMixin, enum.Enum):
                A = 1
                B = 2
                C = 3

        with self.assertRaises(ImportError):
            class ThrowsEnum(
                enum.Enum,
                metaclass=DjangoEnumPropertiesMeta
            ):
                A = 1
                B = 2
                C = 3

        with self.assertRaises(ImportError):
            class ThrowsEnum(IntegerChoices):
                A = 1
                B = 2
                C = 3

        with self.assertRaises(ImportError):
            class ThrowsEnum(TextChoices):
                A = 'A'
                B = 'B'
                C = 'C'

        with self.assertRaises(ImportError):
            class ThrowsEnum(FloatChoices):
                A = 1.1
                B = 2.2
                C = 3.3

        self.do_test_integer_choices()
        self.do_test_text_choices()

    def test_enum_properties_missing(self):
        import sys
        from importlib import reload
        from unittest.mock import patch

        if 'enum_properties' in sys.modules:
            with patch.dict(sys.modules, {'enum_properties': None}):
                from django_enum import choices
                reload(sys.modules['django_enum.choices'])
                self.do_enum_properties_missing()
            reload(sys.modules['django_enum.choices'])
        else:
            self.do_enum_properties_missing()  # pragma: no cover


class TestFieldTypeResolution(EnumTypeMixin, TestCase):

    MODEL_CLASS = EnumTester
    MODEL_FLAG_CLASS = EnumFlagTester

    def test_base_fields(self):
        """
        Test that the Enum metaclass picks the correct database field type for each enum.
        """
        from django.db.models import (
            BigIntegerField,
            BinaryField,
            CharField,
            DateField,
            DateTimeField,
            DecimalField,
            DurationField,
            FloatField,
            IntegerField,
            PositiveBigIntegerField,
            PositiveIntegerField,
            PositiveSmallIntegerField,
            SmallIntegerField,
            TimeField,
        )

        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('small_int'), SmallIntegerField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('small_pos_int'), PositiveSmallIntegerField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('int'), IntegerField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('pos_int'), PositiveIntegerField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('big_int'), BigIntegerField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('big_pos_int'), PositiveBigIntegerField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('extern'), PositiveSmallIntegerField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('text'), CharField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('constant'), FloatField)

        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('small_neg'), SmallIntegerField)
        self.assertNotIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('small_neg'), FlagField)
        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('small_pos'), PositiveSmallIntegerField)
        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('small_pos'), SmallIntegerFlagField)

        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('neg'), IntegerField)
        self.assertNotIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('neg'), FlagField)
        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('pos'), PositiveIntegerField)
        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('pos'), IntegerFlagField)

        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('big_neg'), BigIntegerField)
        self.assertNotIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('big_neg'), FlagField)
        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('big_pos'), PositiveBigIntegerField)
        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('big_pos'), BigIntegerFlagField)

        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('extra_big_neg'), EnumExtraBigIntegerField)
        self.assertNotIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('extra_big_neg'), FlagField)
        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('extra_big_neg'), BinaryField)
        self.assertIsInstance(self.MODEL_FLAG_CLASS._meta.get_field('extra_big_pos'), ExtraBigIntegerFlagField)

        self.assertEqual(self.MODEL_CLASS._meta.get_field('small_int').primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('small_int').bit_length, 16)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('small_pos_int').primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('small_pos_int').bit_length, 15)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('pos_int').primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('pos_int').bit_length, 31)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('int').primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('int').bit_length, 32)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('big_int').primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('big_pos_int').primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('big_pos_int').bit_length, 32)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('big_int').bit_length, 32)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('extern').primitive, int)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('text').primitive, str)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('constant').primitive, float)

        self.assertEqual(self.MODEL_FLAG_CLASS._meta.get_field('small_neg').primitive, int)
        self.assertEqual(self.MODEL_FLAG_CLASS._meta.get_field('small_pos').primitive, int)

        self.assertEqual(self.MODEL_FLAG_CLASS._meta.get_field('neg').primitive, int)
        self.assertEqual(self.MODEL_FLAG_CLASS._meta.get_field('pos').primitive, int)

        self.assertEqual(self.MODEL_FLAG_CLASS._meta.get_field('big_neg').primitive, int)
        self.assertEqual(self.MODEL_FLAG_CLASS._meta.get_field('big_pos').primitive, int)
        self.assertEqual(self.MODEL_FLAG_CLASS._meta.get_field('extra_big_neg').primitive, int)
        self.assertEqual(self.MODEL_FLAG_CLASS._meta.get_field('extra_big_pos').primitive, int)

        # eccentric enums
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('date_enum'), DateField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('datetime_enum'), DateTimeField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('duration_enum'), DurationField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('time_enum'), TimeField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('decimal_enum'), DecimalField)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('decimal_enum').max_digits, 7)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('decimal_enum').decimal_places, 4)

        self.assertEqual(self.MODEL_CLASS._meta.get_field('date_enum').primitive, date)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('datetime_enum').primitive, datetime)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('duration_enum').primitive, timedelta)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('time_enum').primitive, time)
        self.assertEqual(self.MODEL_CLASS._meta.get_field('decimal_enum').primitive, Decimal)
        #

        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('small_int'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('small_pos_int'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('pos_int'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('big_int'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('big_pos_int'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('extern'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('text'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('constant'), EnumField)

        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('date_enum'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('datetime_enum'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('duration_enum'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('time_enum'), EnumField)
        self.assertIsInstance(self.MODEL_CLASS._meta.get_field('decimal_enum'), EnumField)

        tester = self.MODEL_CLASS.objects.create()

        self.assertEqual(tester.small_int, tester._meta.get_field('small_int').default)
        self.assertEqual(tester.small_int, self.SmallIntEnum.VAL3)
        self.assertIsNone(tester.small_pos_int)
        self.assertIsInstance(tester._meta.get_field('int'), IntegerField)
        self.assertIsNone(tester.int)

        self.assertEqual(tester.pos_int, tester._meta.get_field('pos_int').default)
        self.assertEqual(tester.pos_int, self.PosIntEnum.VAL3)

        self.assertEqual(tester.big_int, tester._meta.get_field('big_int').default)
        self.assertEqual(tester.big_int, self.BigIntEnum.VAL0)

        self.assertIsNone(tester.big_pos_int)

        self.assertIsInstance(tester._meta.get_field('constant'), FloatField)
        self.assertIsNone(tester.constant)

        self.assertIsInstance(tester._meta.get_field('text'), CharField)
        self.assertEqual(tester._meta.get_field('text').max_length, 4)
        self.assertIsNone(tester.text)

        self.assertIsNone(tester.extern)


class MiscOffNominalTests(TestCase):

    def test_field_def_errors(self):
        from django.db.models import Model
        with self.assertRaises(ValueError):
            class TestModel(Model):
                enum = EnumField()

    def test_variable_primitive_type(self):
        from enum import Enum

        from django.db.models import Model
        from django_enum.utils import determine_primitive

        class MultiPrimitive(Enum):
            VAL1 = 1
            VAL2 = '2'
            VAL3 = 3.0
            VAL4 = b'4'

        self.assertIsNone(determine_primitive(MultiPrimitive))

        with self.assertRaises(ValueError):
            class TestModel(Model):
                enum = EnumField(MultiPrimitive)

        with self.assertRaises(ValueError):
            """
            2 is not symmetrically convertable float<->str
            """
            class TestModel(Model):
                enum = EnumField(MultiPrimitive, primitive=float)

    def test_unsupported_primitive(self):
        from enum import Enum

        from django_enum.utils import determine_primitive

        class MyPrimitive:
            pass

        class WeirdPrimitive(Enum):
            VAL1 = MyPrimitive()
            VAL2 = MyPrimitive()
            VAL3 = MyPrimitive()

        self.assertEqual(determine_primitive(WeirdPrimitive), MyPrimitive)

        with self.assertRaises(NotImplementedError):
            EnumField(WeirdPrimitive)

    def test_bit_length_override(self):
        from enum import IntFlag

        class IntEnum(IntFlag):
            VAL1 = 2**0
            VAL2 = 2**2
            VAL3 = 2**3
            VAL8 = 2**8

        with self.assertRaises(AssertionError):
            EnumField(IntEnum, bit_length=7)

        field = EnumField(IntEnum, bit_length=12)
        self.assertEqual(field.bit_length, 12)

    def test_no_value_enum(self):
        from enum import Enum
        from django_enum.utils import determine_primitive

        class EmptyEnum(Enum):
            pass

        self.assertIsNone(determine_primitive(EmptyEnum))

        with self.assertRaises(ValueError):
            EnumField(EmptyEnum)

    def test_copy_field(self):
        from enum import Enum
        from copy import copy, deepcopy

        class BasicEnum(Enum):
            VAL1 = '1'
            VAL2 = '2'
            VAL3 = '3'

        field = EnumField(BasicEnum)
        field2 = deepcopy(field)
        field3 = copy(field)

        self.assertEqual(field.enum, field2.enum, field3.enum)


class TestEmptyEnumValues(TestCase):

    def test_none_enum_values(self):
        # TODO??
        pass


class TestEnumQueries(EnumTypeMixin, TestCase):

    MODEL_CLASS = EnumTester

    def setUp(self):
        self.MODEL_CLASS.objects.all().delete()

        self.MODEL_CLASS.objects.create(
            small_pos_int=self.SmallPosIntEnum.VAL2,
            small_int=self.SmallIntEnum.VAL0,
            pos_int=self.PosIntEnum.VAL1,
            int=self.IntEnum.VALn1,
            big_pos_int=self.BigPosIntEnum.VAL3,
            big_int=self.BigIntEnum.VAL2,
            constant=self.Constants.GOLDEN_RATIO,
            text=self.TextEnum.VALUE2,
            extern=self.ExternEnum.ONE
        )
        self.MODEL_CLASS.objects.create(
            small_pos_int=self.SmallPosIntEnum.VAL2,
            small_int=self.SmallIntEnum.VAL0,
            pos_int=self.PosIntEnum.VAL1,
            int=self.IntEnum.VALn1,
            big_pos_int=self.BigPosIntEnum.VAL3,
            big_int=self.BigIntEnum.VAL2,
            constant=self.Constants.GOLDEN_RATIO,
            text=self.TextEnum.VALUE2,
            extern=self.ExternEnum.ONE
        )

        self.MODEL_CLASS.objects.create()

    def test_query(self):

        self.assertEqual(self.MODEL_CLASS.objects.filter(small_pos_int=self.SmallPosIntEnum.VAL2).count(), 2)
        self.assertEqual(self.MODEL_CLASS.objects.filter(small_pos_int=self.SmallPosIntEnum.VAL2.value).count(), 2)

        self.assertEqual(self.MODEL_CLASS.objects.filter(big_pos_int=self.BigPosIntEnum.VAL3).count(), 2)
        self.assertEqual(self.MODEL_CLASS.objects.filter(big_pos_int=None).count(), 1)

        self.assertEqual(self.MODEL_CLASS.objects.filter(constant=self.Constants.GOLDEN_RATIO).count(), 2)
        self.assertEqual(self.MODEL_CLASS.objects.filter(constant=self.Constants.GOLDEN_RATIO.value).count(), 2)
        self.assertEqual(self.MODEL_CLASS.objects.filter(constant__isnull=True).count(), 1)

        self.assertEqual(self.MODEL_CLASS.objects.filter(text=self.TextEnum.VALUE2).count(), 2)

        self.assertEqual(self.MODEL_CLASS.objects.filter(extern=self.ExternEnum.ONE).count(), 2)
        self.assertEqual(self.MODEL_CLASS.objects.filter(extern=self.ExternEnum.TWO).count(), 0)

        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, int_field='a')
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, float_field='a')
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, constant='Pi')
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, big_pos_int='Val3')
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, big_pos_int=type('WrongType')())


class TestFormField(EnumTypeMixin, TestCase):

    MODEL_CLASS = EnumTester
    FORM_CLASS = EnumTesterForm
    form_type = None

    @property
    def model_params(self):
        return {
            'small_pos_int': 0,
            'small_int': self.SmallIntEnum.VAL2,
            'pos_int': 2147483647,
            'int': self.IntEnum.VALn1,
            'big_pos_int': 2,
            'big_int': self.BigIntEnum.VAL0,
            'constant': 2.71828,
            'text': self.TextEnum.VALUE3,
            'extern': self.ExternEnum.THREE,
            'date_enum': self.DateEnum.BRIAN,
            'datetime_enum': self.DateTimeEnum.ST_HELENS,
            'duration_enum': self.DurationEnum.FORTNIGHT,
            'time_enum': self.TimeEnum.COB,
            'decimal_enum': self.DecimalEnum.ONE,
            'dj_int_enum': 2,
            'dj_text_enum': self.DJTextEnum.B,
            'non_strict_int': self.SmallPosIntEnum.VAL2,
            'non_strict_text': 'arbitrary',
            'no_coerce': self.SmallPosIntEnum.VAL1
        }

    @property
    def bad_values(self):
        return {
            'small_pos_int': 4.1,
            'small_int': 'Value 12',
            'pos_int': 5.3,
            'int': 10,
            'big_pos_int': '-12',
            'big_int': '-12',
            'constant': 2.7,
            'text': '143 emma',
            'date_enum': '20159-01-01',
            'datetime_enum': 'AAAA-01-01 00:00:00',
            'duration_enum': '1 elephant',
            'time_enum': '2.a',
            'decimal_enum': 'alpha',
            'extern': 6,
            'dj_int_enum': '',
            'dj_text_enum': 'D',
            'non_strict_int': 'Not an int',
            'non_strict_text': 'A' * 13,
            'no_coerce': 'Value 0',
        }

    from json import encoder

    def verify_field(self, form, field, value):
        # this doesnt work with coerce=False fields
        if self.MODEL_CLASS._meta.get_field(field).coerce:
            self.assertIsInstance(form[field].value(), self.enum_primitive(field))
        #######
        if self.MODEL_CLASS._meta.get_field(field).strict:
            self.assertEqual(
                form[field].value(),
                self.enum_type(field)(value).value
            )
            if self.MODEL_CLASS._meta.get_field(field).coerce:
                self.assertIsInstance(
                    form[field].field.to_python(form[field].value()),
                    self.enum_type(field)
                )
        else:
            self.assertEqual(form[field].value(), value)

    def test_initial(self):
        form = self.FORM_CLASS(initial=self.model_params)
        for field, value in self.model_params.items():
            self.verify_field(form, field, value)

    def test_instance(self):
        instance = self.MODEL_CLASS.objects.create(**self.model_params)
        form = self.FORM_CLASS(instance=instance)
        for field, value in self.model_params.items():
            self.verify_field(form, field, value)
        instance.delete()

    def test_data(self):
        form = self.FORM_CLASS(data=self.model_params)
        form.full_clean()
        self.assertTrue(form.is_valid())
        for field, value in self.model_params.items():
            self.verify_field(form, field, value)

    def test_error(self):
        for field, bad_value in self.bad_values.items():
            form = self.FORM_CLASS(
                data={
                    **self.model_params,
                    field: bad_value
                }
            )
            form.full_clean()
            self.assertFalse(form.is_valid())
            self.assertTrue(field in form.errors)

        form = self.FORM_CLASS(data=self.bad_values)
        form.full_clean()
        self.assertFalse(form.is_valid())
        for field in self.bad_values.keys():
            self.assertTrue(field in form.errors)

    def test_field_validation(self):
        for enum_field, bad_value in [
            (EnumChoiceField(self.SmallPosIntEnum), 4.1),
            (EnumChoiceField(self.SmallIntEnum), 123123123),
            (EnumChoiceField(self.PosIntEnum), -1),
            (EnumChoiceField(self.IntEnum), '63'),
            (EnumChoiceField(self.BigPosIntEnum), None),
            (EnumChoiceField(self.BigIntEnum), ''),
            (EnumChoiceField(self.Constants), 'y'),
            (EnumChoiceField(self.TextEnum), 42),
            (EnumChoiceField(self.DateEnum), '20159-01-01'),
            (EnumChoiceField(self.DateTimeEnum), 'AAAA-01-01 00:00:00'),
            (EnumChoiceField(self.DurationEnum), '1 elephant'),
            (EnumChoiceField(self.TimeEnum), '2.a'),
            (EnumChoiceField(self.DecimalEnum), 'alpha'),
            (EnumChoiceField(self.ExternEnum), 0),
            (EnumChoiceField(self.DJIntEnum), '5.3'),
            (EnumChoiceField(self.DJTextEnum), 12),
            (EnumChoiceField(self.SmallPosIntEnum, strict=False), 'not an int')
        ]:
            self.assertRaises(ValidationError, enum_field.validate, bad_value)

        for enum_field, bad_value in [
            (EnumChoiceField(self.SmallPosIntEnum, strict=False), 4),
            (EnumChoiceField(self.SmallIntEnum, strict=False), 123123123),
            (EnumChoiceField(self.PosIntEnum, strict=False), -1),
            (EnumChoiceField(self.IntEnum, strict=False), '63'),
            (EnumChoiceField(self.BigPosIntEnum, strict=False), 18),
            (EnumChoiceField(self.BigIntEnum, strict=False), '-8'),
            (EnumChoiceField(self.Constants, strict=False), '1.976'),
            (EnumChoiceField(self.TextEnum, strict=False), 42),
            (EnumChoiceField(self.ExternEnum, strict=False), 0),
            (EnumChoiceField(self.DJIntEnum, strict=False), '5'),
            (EnumChoiceField(self.DJTextEnum, strict=False), 12),
            (EnumChoiceField(self.SmallPosIntEnum, strict=False), '12'),
            (EnumChoiceField(self.DateEnum, strict=False), date(year=2015, month=1, day=1)),
            (EnumChoiceField(self.DateTimeEnum, strict=False), datetime(year=2014, month=1, day=1, hour=0, minute=0, second=0)),
            (EnumChoiceField(self.DurationEnum, strict=False), timedelta(seconds=15)),
            (EnumChoiceField(self.TimeEnum, strict=False), time(hour=2, minute=0, second=0)),
            (EnumChoiceField(self.DecimalEnum, strict=False), Decimal('0.5')),
        ]:
            try:
                enum_field.clean(bad_value)
            except ValidationError:  # pragma: no cover
                self.fail(f'non-strict choice field for {enum_field.enum} raised ValidationError on {bad_value} during clean')

    def test_non_strict_field(self):
        form = self.FORM_CLASS(
            data={
                **self.model_params,
                'non_strict_int': 200
            }
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
        self.assertIsInstance(
            form['non_strict_int'].value(),
            self.enum_primitive('non_strict_int')
        )
        self.assertEqual(
            form['non_strict_int'].value(),
            200
        )
        self.assertIsInstance(
            form['non_strict_int'].field.to_python(form['non_strict_int'].value()),
            self.enum_primitive('non_strict_int')
        )


class TestRequests(EnumTypeMixin, TestCase):

    MODEL_CLASS = EnumTester
    NAMESPACE = 'django_enum_tests_djenum'

    objects = []
    values = {}

    maxDiff = None

    fields = [
        'small_pos_int',
        'small_int',
        'pos_int',
        'int',
        'big_pos_int',
        'big_int',
        'constant',
        'text',
        'extern',
        'date_enum',
        'datetime_enum',
        'duration_enum',
        'time_enum',
        'decimal_enum',
        'dj_int_enum',
        'dj_text_enum',
        'non_strict_int',
        'non_strict_text',
        'no_coerce',
    ]

    def setUp(self):
        self.values = {val: {} for val in self.compared_attributes}
        self.objects = []
        self.MODEL_CLASS.objects.all().delete()
        self.objects.append(
            self.MODEL_CLASS.objects.create()
        )
        self.objects[-1].refresh_from_db()

        self.objects.append(
            self.MODEL_CLASS.objects.create(
                small_pos_int=self.SmallPosIntEnum.VAL1,
                small_int=self.SmallIntEnum.VAL1,
                pos_int=self.PosIntEnum.VAL1,
                int=self.IntEnum.VAL1,
                big_pos_int=self.BigPosIntEnum.VAL1,
                big_int=self.BigIntEnum.VAL1,
                constant=self.Constants.PI,
                text=self.TextEnum.VALUE1,
                date_enum=self.DateEnum.BRIAN,
                datetime_enum=self.DateTimeEnum.PINATUBO,
                duration_enum=self.DurationEnum.WEEK,
                time_enum=self.TimeEnum.LUNCH,
                decimal_enum=self.DecimalEnum.TWO,
                extern=self.ExternEnum.ONE,
                non_strict_int=self.SmallPosIntEnum.VAL1,
                non_strict_text=self.TextEnum.VALUE1,
                no_coerce=self.SmallPosIntEnum.VAL1
            )
        )
        self.objects[-1].refresh_from_db()

        for _ in range(0, 2):
            self.objects.append(
                self.MODEL_CLASS.objects.create(
                    small_pos_int=self.SmallPosIntEnum.VAL2,
                    small_int=self.SmallIntEnum.VAL2,
                    pos_int=self.PosIntEnum.VAL2,
                    int=self.IntEnum.VAL2,
                    big_pos_int=self.BigPosIntEnum.VAL2,
                    big_int=self.BigIntEnum.VAL2,
                    constant=self.Constants.e,
                    text=self.TextEnum.VALUE2,
                    extern=self.ExternEnum.TWO,
                    date_enum=self.DateEnum.EMMA,
                    datetime_enum=self.DateTimeEnum.ST_HELENS,
                    duration_enum=self.DurationEnum.DAY,
                    time_enum=self.TimeEnum.MORNING,
                    decimal_enum=self.DecimalEnum.ONE,
                    non_strict_int=self.SmallPosIntEnum.VAL2,
                    non_strict_text=self.TextEnum.VALUE2,
                    no_coerce=self.SmallPosIntEnum.VAL2
                )
            )
            self.objects[-1].refresh_from_db()

        for _ in range(0, 3):
            self.objects.append(
                self.MODEL_CLASS.objects.create(
                    small_pos_int=self.SmallPosIntEnum.VAL3,
                    small_int=self.SmallIntEnum.VAL3,
                    pos_int=self.PosIntEnum.VAL3,
                    int=self.IntEnum.VAL3,
                    big_pos_int=self.BigPosIntEnum.VAL3,
                    big_int=self.BigIntEnum.VAL3,
                    constant=self.Constants.GOLDEN_RATIO,
                    text=self.TextEnum.VALUE3,
                    extern=self.ExternEnum.THREE,
                    date_enum=self.DateEnum.HUGO,
                    datetime_enum=self.DateTimeEnum.KATRINA,
                    duration_enum=self.DurationEnum.FORTNIGHT,
                    time_enum=self.TimeEnum.COB,
                    decimal_enum=self.DecimalEnum.FIVE,
                    non_strict_int=self.SmallPosIntEnum.VAL3,
                    non_strict_text=self.TextEnum.VALUE3,
                    no_coerce=self.SmallPosIntEnum.VAL3
                )
            )
            self.objects[-1].refresh_from_db()

        self.objects.append(
            self.MODEL_CLASS.objects.create(
                non_strict_int=88,
                non_strict_text='arbitrary'
            )
        )

        for obj in self.objects:
            for attr in self.values.keys():
                self.values[attr].setdefault(getattr(obj, attr), [])
                self.values[attr][getattr(obj, attr)].append(obj.pk)

    def tearDown(self):
        self.MODEL_CLASS.objects.all().delete()


    @property
    def post_params(self):
        return {
            'small_pos_int': self.SmallPosIntEnum.VAL2,
            'small_int': self.SmallIntEnum.VAL0,
            'pos_int': self.PosIntEnum.VAL1,
            'int': self.IntEnum.VALn1,
            'big_pos_int': self.BigPosIntEnum.VAL2,
            'big_int': self.BigIntEnum.VAL2,
            'constant': self.Constants.GOLDEN_RATIO,
            'text': self.TextEnum.VALUE2,
            'extern': self.ExternEnum.TWO,
            'date_enum': self.DateEnum.EMMA.value,
            'datetime_enum': self.DateTimeEnum.ST_HELENS.value,
            'duration_enum': self.DurationEnum.DAY.value,
            'time_enum': self.TimeEnum.MORNING.value,
            'decimal_enum': self.DecimalEnum.ONE.value,
            'dj_int_enum': self.DJIntEnum.TWO,
            'dj_text_enum': self.DJTextEnum.C,
            'non_strict_int': self.SmallPosIntEnum.VAL1,
            'non_strict_text': self.TextEnum.VALUE3,
            'no_coerce': self.SmallPosIntEnum.VAL3
        }

    @property
    def post_params_symmetric(self):
        return {
            **self.post_params,
        }

    if DJANGO_RESTFRAMEWORK_INSTALLED:  # pragma: no cover

        def test_non_strict_drf_field(self):
            from django_enum.drf import EnumField
            from rest_framework import fields

            field = EnumField(self.SmallPosIntEnum, strict=False)
            self.assertEqual(field.to_internal_value('1'), 1)
            self.assertEqual(field.to_representation(1), 1)
            self.assertEqual(
                field.primitive_field.__class__,
                fields.IntegerField
            )

            field = EnumField(self.Constants, strict=False)
            self.assertEqual(field.to_internal_value('5.43'), 5.43)
            self.assertEqual(field.to_representation(5.43), 5.43)
            self.assertEqual(
                field.primitive_field.__class__,
                fields.FloatField
            )

            field = EnumField(self.TextEnum, strict=False)
            self.assertEqual(field.to_internal_value('random text'), 'random text')
            self.assertEqual(field.to_representation('random text'), 'random text')
            self.assertEqual(
                field.primitive_field.__class__,
                fields.CharField
            )

            field = EnumField(self.DateEnum, strict=False)
            self.assertEqual(field.to_internal_value('2017-12-05'), date(year=2017, day=5, month=12))
            self.assertEqual(field.to_representation(date(year=2017, day=5, month=12)), date(year=2017, day=5, month=12))
            self.assertEqual(
                field.primitive_field.__class__,
                fields.DateField
            )

            field = EnumField(self.DateTimeEnum, strict=False)
            self.assertEqual(field.to_internal_value('2017-12-05T01:02:30Z'), datetime(year=2017, day=5, month=12, hour=1, minute=2, second=30))
            self.assertEqual(
                field.to_representation(
                    datetime(year=2017, day=5, month=12, hour=1, minute=2, second=30)
                ),
                datetime(year=2017, day=5, month=12, hour=1, minute=2, second=30)
            )
            self.assertEqual(
                field.primitive_field.__class__,
                fields.DateTimeField
            )

            field = EnumField(self.DurationEnum, strict=False)
            self.assertEqual(field.to_internal_value('P5DT01H00M01.312500S'), timedelta(days=5, hours=1, seconds=1.3125))
            self.assertEqual(
                field.to_representation(
                    timedelta(days=5, hours=1, seconds=1.3125)
                ),
                timedelta(days=5, hours=1, seconds=1.3125)
            )
            self.assertEqual(
                field.primitive_field.__class__,
                fields.DurationField
            )

            field = EnumField(self.TimeEnum, strict=False)
            self.assertEqual(field.to_internal_value('01:02:30'), time(hour=1, minute=2, second=30))
            self.assertEqual(
                field.to_representation(
                    time(hour=1, minute=2, second=30)
                ),
                time(hour=1, minute=2, second=30)
            )
            self.assertEqual(
                field.primitive_field.__class__,
                fields.TimeField
            )

            field = EnumField(self.DecimalEnum, strict=False)
            self.assertEqual(field.to_internal_value('1.67'), Decimal('1.67'))
            self.assertEqual(
                field.to_representation(Decimal('1.67')),
                Decimal('1.67')
            )
            self.assertEqual(
                field.primitive_field.__class__,
                fields.DecimalField
            )

            from enum import Enum

            class UnsupportedPrimitiveEnum(Enum):

                VAL1 = (1,)
                VAL2 = (1, 2)
                VAL3 = (1, 2, 3)

            field = EnumField(
                UnsupportedPrimitiveEnum,
                strict=False,
                choices=[
                    (UnsupportedPrimitiveEnum.VAL1, 'VAL1'),
                    (UnsupportedPrimitiveEnum.VAL2, 'VAL2'),
                    (UnsupportedPrimitiveEnum.VAL3, 'VAL3'),
                ]
            )
            self.assertEqual(field.to_internal_value((1, 2, 4)), (1, 2, 4))
            self.assertEqual(
                field.to_representation((1, 2, 4)),
                (1, 2, 4)
            )
            self.assertIsNone(field.primitive_field)

        def test_drf_serializer(self):

            from django_enum.drf import EnumField
            from rest_framework import serializers

            class TestSerializer(serializers.ModelSerializer):

                small_pos_int = EnumField(self.SmallPosIntEnum)
                small_int = EnumField(self.SmallIntEnum)
                pos_int = EnumField(self.PosIntEnum)
                int = EnumField(self.IntEnum)
                big_pos_int = EnumField(self.BigPosIntEnum)
                big_int = EnumField(self.BigIntEnum)
                constant = EnumField(self.Constants)
                date_enum = EnumField(self.DateEnum)
                datetime_enum = EnumField(self.DateTimeEnum, strict=False)
                duration_enum = EnumField(self.DurationEnum)
                time_enum = EnumField(self.TimeEnum)
                decimal_enum = EnumField(self.DecimalEnum)
                text = EnumField(self.TextEnum)
                extern = EnumField(self.ExternEnum)
                dj_int_enum = EnumField(self.DJIntEnum)
                dj_text_enum = EnumField(self.DJTextEnum)
                non_strict_int = EnumField(self.SmallPosIntEnum, strict=False)
                non_strict_text = EnumField(
                    self.TextEnum,
                    strict=False,
                    allow_blank=True
                )
                no_coerce = EnumField(self.SmallPosIntEnum)

                class Meta:
                    model = self.MODEL_CLASS
                    fields = '__all__'

            ser = TestSerializer(data=self.post_params)
            self.assertTrue(ser.is_valid())
            inst = ser.save()
            for param, value in self.post_params.items():
                self.assertEqual(value, getattr(inst, param))

            ser_bad = TestSerializer(
                data={
                    **self.post_params,
                    'small_pos_int': -1,
                    'constant': 3.14,
                    'text': 'wrong',
                    'extern': 0,
                    'pos_int': -50,
                    'date_enum': date(year=2017, day=5, month=12),
                    'decimal_enum': Decimal('1.89')
                }
            )

            self.assertFalse(ser_bad.is_valid())
            self.assertTrue('small_pos_int' in ser_bad.errors)
            self.assertTrue('constant' in ser_bad.errors)
            self.assertTrue('text' in ser_bad.errors)
            self.assertTrue('extern' in ser_bad.errors)
            self.assertTrue('pos_int' in ser_bad.errors)
            self.assertTrue('date_enum' in ser_bad.errors)
            self.assertTrue('decimal_enum' in ser_bad.errors)

        def test_drf_read(self):
            c = Client()
            response = c.get(reverse(f'{self.NAMESPACE}:enumtester-list'))
            read_objects = response.json()
            self.assertEqual(len(read_objects), len(self.objects))

            for idx, obj in enumerate(response.json()):
                # should be same order
                self.assertEqual(obj['id'], self.objects[idx].id)
                for field in self.fields:
                    self.assertEqual(obj[field], getattr(self.objects[idx], field))
                    if obj[field] is not None:
                        self.assertIsInstance(
                            try_convert(self.enum_primitive(field), obj[field], raise_on_error=False),
                            self.enum_primitive(field)
                        )

        def test_drf_update(self):
            c = Client()
            params = self.post_params_symmetric
            response = c.put(
                reverse(
                    f'{self.NAMESPACE}:enumtester-detail',
                    kwargs={'pk': self.objects[0].id}
                ),
                params,
                follow=True,
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            fetched = c.get(
                reverse(
                    f'{self.NAMESPACE}:enumtester-detail',
                    kwargs={'pk': self.objects[0].id}
                ),
                follow=True
            ).json()

            obj = self.MODEL_CLASS.objects.get(pk=self.objects[0].id)

            self.assertEqual(fetched['id'], obj.id)
            for field in self.fields:
                self.assertEqual(try_convert(self.enum_primitive(field), fetched[field], raise_on_error=False), getattr(obj, field))
                if self.MODEL_CLASS._meta.get_field(field).coerce:
                    self.assertEqual(params[field], getattr(obj, field))

        def test_drf_post(self):
            c = Client()
            params = {
                **self.post_params_symmetric,
                'non_strict_text': '',
                'text': None
            }
            response = c.post(
                reverse(f'{self.NAMESPACE}:enumtester-list'),
                params,
                follow=True,
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
            created = response.json()

            obj = self.MODEL_CLASS.objects.last()

            self.assertEqual(created['id'], obj.id)
            for field in self.fields:
                self.assertEqual(getattr(obj, field), try_convert(self.enum_primitive(field), created[field], raise_on_error=False))
                if self.MODEL_CLASS._meta.get_field(field).coerce:
                    self.assertEqual(getattr(obj, field), params[field])

    else:
        pass  # pragma: no cover

    def test_add(self):
        """
        Test that add forms work and that EnumField type allows creations
        from symmetric values
        """
        c = Client()

        # test normal choice field and our EnumChoiceField
        form_url = 'enum-add'
        params = self.post_params_symmetric
        response = c.post(
            reverse(f'{self.NAMESPACE}:{form_url}'),
            params,
            follow=True
        )
        soup = Soup(response.content, features='html.parser')
        added_resp = soup.find_all('div', class_='enum')[-1]
        added = self.MODEL_CLASS.objects.last()

        for param, value in params.items():
            form_val = added_resp.find(class_=param).find("span", class_="value").text
            try:
                form_val = self.enum_primitive(param)(form_val)
            except (TypeError, ValueError):
                if form_val:
                    form_val = try_convert(
                        self.enum_primitive(param),
                        form_val,
                        raise_on_error=True
                    )
                else:  # pragma: no cover
                    pass
            if self.MODEL_CLASS._meta.get_field(param).strict:
                self.assertEqual(
                    self.enum_type(param)(form_val),
                    self.enum_type(param)(value)
                )
            else:
                self.assertEqual(form_val, value)
            self.assertEqual(getattr(added, param), form_val)
        added.delete()

    def test_update(self):
        """
        Test that update forms work and that EnumField type allows updates
        from symmetric values
        """
        c = Client()

        # test normal choice field and our EnumChoiceField
        form_url = 'enum-update'
        params = self.post_params_symmetric
        updated = self.MODEL_CLASS.objects.create()
        response = c.post(
            reverse(f'{self.NAMESPACE}:{form_url}', kwargs={'pk': updated.pk}),
            data=params,
            follow=True
        )
        updated.refresh_from_db()
        soup = Soup(response.content, features='html.parser')
        self.verify_form(updated, soup)

        for param, value in params.items():
            if not self.MODEL_CLASS._meta.get_field(param).coerce and self.MODEL_CLASS._meta.get_field(param).strict:
                value = self.enum_type(param)(value)
            self.assertEqual(getattr(updated, param), value)
        updated.delete()

    def test_delete(self):
        c = Client()
        form_url = 'enum-delete'
        deleted = self.MODEL_CLASS.objects.create()
        c.delete(reverse(f'{self.NAMESPACE}:{form_url}', kwargs={'pk': deleted.pk}))
        self.assertRaises(self.MODEL_CLASS.DoesNotExist, self.MODEL_CLASS.objects.get, pk=deleted.pk)

    def get_enum_val(self, enum, value, primitive, null=True, coerce=True, strict=True):
        try:
            if coerce:
                if value is None or value == '':
                    return None if null else ''
                if int in enum.__mro__:
                    return enum(int(value))
                if float in enum.__mro__:
                    return enum(float(value))
                return enum(value)
        except ValueError as err:
            if strict:  # pragma: no cover
                raise err

        if value not in {None, ''}:
            try:
                return try_convert(primitive, value, raise_on_error=True)
            except ValueError as err:
                return primitive(value)
        return None if null else ''

    def test_add_form(self):
        c = Client()
        # test normal choice field and our EnumChoiceField
        form_url = 'enum-add'
        response = c.get(reverse(f'{self.NAMESPACE}:{form_url}'))
        soup = Soup(response.content, features='html.parser')
        self.verify_form(self.MODEL_CLASS(), soup)

    def verify_form(self, obj, soup):
        """
        Verify form structure, options and selected values reflect object.

        :param obj: The model object if this is an update form, None if it's a
            create form
        :param soup: The html form for the object
        :return:
        """
        for field in self.fields:
            field = self.MODEL_CLASS._meta.get_field(field)

            expected = {}
            for en in field.enum:
                for val, label in field.choices:
                    if en == val:
                        expected[en if field.coerce else val] = label

            if (
                not any([getattr(obj, field.name) == exp for exp in expected])
                and getattr(obj, field.name) not in {None, ''}
            ):
                # add any non-strict values
                expected[getattr(obj, field.name)] = str(getattr(obj, field.name))
                self.assertFalse(field.strict)

            null_opt = False
            for option in soup.find(
                    'select',
                    id=f'id_{field.name}'
            ).find_all('option'):

                if (
                    option['value'] is None or option['value'] == ''
                ) and option.text.count('-') >= 2:
                    self.assertTrue(field.blank or field.null)
                    null_opt = True
                    if option.has_attr('selected'):
                        self.assertTrue(getattr(obj, field.name) in {None, ''})
                    if getattr(obj, field.name) == option['value']:
                        self.assertTrue(option.has_attr('selected'))
                    # (coverage error?? the line below gets hit)
                    continue  # pragma: no cover

                try:
                    try:
                        value = self.get_enum_val(
                            field.enum,
                            option['value'],
                            primitive=self.enum_primitive(field.name),
                            null=field.null,
                            coerce=field.coerce,
                            strict=field.strict
                        )
                    except ValueError:   # pragma: no cover
                        self.assertFalse(field.strict)
                        value = self.enum_primitive(field.name)(option['value'])
                    self.assertEqual(str(expected[value]), option.text)
                    if option.has_attr('selected'):
                        self.assertEqual(getattr(obj, field.name), value)
                    if (
                        getattr(obj, field.name) == value and not (
                            # problem if our enum compares equal to null
                            getattr(obj, field.name) is None and field.null
                        )
                    ):
                        self.assertTrue(option.has_attr('selected'))
                    del expected[value]
                except KeyError:  # pragma: no cover
                    self.fail(
                        f'{field.name} did not expect option '
                        f'{option["value"]}: {option.text}.'
                    )

            self.assertEqual(len(expected), 0)

            if not field.blank:
                self.assertFalse(
                    null_opt,
                    f"An unexpected null option is present on {field.name}"
                )
            elif field.blank:  # pragma: no cover
                self.assertTrue(
                    null_opt,
                    f"Expected a null option on field {field.name}, but none was present."
                )

    def test_update_form(self):
        client = Client()
        # test normal choice field and our EnumChoiceField
        form_url = 'enum-update'
        for obj in self.objects:
            response = client.get(reverse(f'{self.NAMESPACE}:{form_url}', kwargs={'pk': obj.pk}))
            soup = Soup(response.content, features='html.parser')
            self.verify_form(obj, soup)

    def test_non_strict_select(self):
        client = Client()
        obj = self.MODEL_CLASS.objects.create(
            non_strict_int=233
        )
        form_url = 'enum-update'
        response = client.get(
            reverse(
                f'{self.NAMESPACE}:{form_url}',
                kwargs={'pk': obj.pk}
            )
        )
        soup = Soup(response.content, features='html.parser')
        self.verify_form(obj, soup)
        for option in soup.find(
            'select',
            id=f'id_non_strict_int'
        ).find_all('option'):
            if option.has_attr('selected'):
                self.assertEqual(option['value'], '233')

    @property
    def field_filter_properties(self):
        return {
            'small_pos_int': ['value'],
            'small_int': ['value'],
            'pos_int': ['value'],
            'int': ['value'],
            'big_pos_int': ['value'],
            'big_int': ['value'],
            'constant': ['value'],
            'text': ['value'],
            'date_enum': ['value'],
            'datetime_enum': ['value'],
            'time_enum': ['value'],
            'duration_enum': ['value'],
            'decimal_enum': ['value'],
            'extern': ['value'],
            'dj_int_enum': ['value'],
            'dj_text_enum': ['value'],
            'non_strict_int': ['value'],
            'non_strict_text': ['value'],
            'no_coerce': ['value']
        }

    @property
    def compared_attributes(self):
        return [
            'small_pos_int',
            'small_int',
            'pos_int',
            'int',
            'big_pos_int',
            'big_int',
            'constant',
            'text',
            'date_enum',
            'datetime_enum',
            'time_enum',
            'duration_enum',
            'decimal_enum',
            'extern',
            'dj_int_enum',
            'dj_text_enum',
            'non_strict_int',
            'non_strict_text',
            'no_coerce'
        ]

    def list_to_objects(self, resp_content):
        objects = {}
        for obj_div in resp_content.find('body').find_all(f'div', class_='enum'):
            objects[int(obj_div['data-obj-id'])] = {
                attr: self.get_enum_val(
                    self.MODEL_CLASS._meta.get_field(attr).enum,
                    obj_div.find(f'p', {'class': attr}).find(
                        'span', class_='value'
                    ).text,
                    primitive=self.enum_primitive(attr),
                    null=self.MODEL_CLASS._meta.get_field(attr).null,
                    coerce=self.MODEL_CLASS._meta.get_field(attr).coerce,
                    strict=self.MODEL_CLASS._meta.get_field(attr).strict
                )
                for attr in self.compared_attributes
            }
        return objects

    if DJANGO_FILTERS_INSTALLED:
        def test_django_filter(self):
            self.do_test_django_filter(
                reverse(f'{self.NAMESPACE}:enum-filter')
            )

        def do_test_django_filter(self, url, skip_non_strict=True):
            """
            Exhaustively test query parameter permutations based on data
            created in setUp
            """
            client = Client()
            for attr, val_map in self.values.items():
                for val, objs in val_map.items():
                    if (
                        skip_non_strict and not
                        self.MODEL_CLASS._meta.get_field(attr).strict and not
                        any([val == en for en in self.MODEL_CLASS._meta.get_field(attr).enum])
                    ):
                        continue
                    if val in {None, ''}:
                        # todo how to query None or empty?
                        continue
                    for prop in self.field_filter_properties[attr]:
                        qry = QueryDict(mutable=True)
                        try:
                            prop_vals = getattr(val, prop)
                        except AttributeError:
                            prop_vals = val
                        if not isinstance(prop_vals, (set, list)):
                            prop_vals = [prop_vals]
                        for prop_val in prop_vals:
                            qry[attr] = prop_val
                            objects = {
                                obj.pk: {
                                    attr: getattr(obj, attr)
                                    for attr in self.compared_attributes
                                } for obj in
                                self.MODEL_CLASS.objects.filter(id__in=objs)
                            }
                            self.assertEqual(len(objects), len(objs))
                            response = client.get(f'{url}?{qry.urlencode()}')
                            resp_objects = self.list_to_objects(
                                Soup(response.content, features='html.parser')
                            )
                            self.assertEqual(objects, resp_objects)
    else:
        pass  # pragma: no cover


class TestBulkOperations(EnumTypeMixin, TestCase):
    """Tests bulk insertions and updates"""

    MODEL_CLASS = EnumTester
    NUMBER = 250

    def setUp(self):
        self.MODEL_CLASS.objects.all().delete()

    @property
    def create_params(self):
        return {
            'small_pos_int': self.SmallPosIntEnum.VAL2,
            'small_int': self.SmallIntEnum.VALn1,
            'pos_int': 2147483647,
            'int': -2147483648,
            'big_pos_int': self.BigPosIntEnum.VAL3,
            'big_int': self.BigIntEnum.VAL2,
            'constant': self.Constants.GOLDEN_RATIO,
            'text': self.TextEnum.VALUE2,
            'extern': self.ExternEnum.TWO,
            'date_enum': self.DateEnum.HUGO,
            'datetime_enum': self.DateTimeEnum.KATRINA,
            'time_enum': self.TimeEnum.COB,
            'duration_enum': self.DurationEnum.FORTNIGHT,
            'decimal_enum': self.DecimalEnum.FIVE,
            'dj_int_enum': 3,
            'dj_text_enum': self.DJTextEnum.A,
            'non_strict_int': 15,
            'non_strict_text': 'arbitrary',
            'no_coerce': '0'
        }

    @property
    def update_params(self):
        return {
            'non_strict_int': 100,
            'constant': self.Constants.PI,
            'big_int': -2147483649,
            'date_enum': self.DateEnum.BRIAN,
            'datetime_enum': self.DateTimeEnum.ST_HELENS,
            'time_enum': self.TimeEnum.LUNCH,
            'duration_enum': self.DurationEnum.WEEK,
            'decimal_enum': self.DecimalEnum.TWO,
        }

    def test_bulk_create(self):

        objects = []
        for obj in range(0, self.NUMBER):
            objects.append(self.MODEL_CLASS(**self.create_params))

        self.MODEL_CLASS.objects.bulk_create(objects)

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(**self.create_params).count(),
            self.NUMBER
        )

    def test_bulk_update(self):
        objects = []
        for obj in range(0, self.NUMBER):
            obj = self.MODEL_CLASS.objects.create(**self.create_params)
            for param, value in self.update_params.items():
                setattr(obj, param, value)
            objects.append(obj)

        self.assertEqual(len(objects), self.NUMBER)
        to_update = ['constant', 'non_strict_int']
        self.MODEL_CLASS.objects.bulk_update(objects, to_update)

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                **{
                    **self.create_params,
                    **{
                        param: val for param, val in self.update_params.items()
                        if param in to_update
                    }
                }
            ).count(),
            self.NUMBER
        )


class FlagTests(TestCase):

    MODEL_CLASS = EnumFlagTester

    def test_flag_filters(self):
        fields = [
            field for field in self.MODEL_CLASS._meta.fields
            if isinstance(field, EnumField)
        ]

        # keep track of empty counts for filter assertions
        empties = {field.name: 0 for field in fields}

        def update_empties(obj):
            for field in fields:
                value = getattr(obj, field.name)
                if value is not None and int(value) == 0:
                    empties[field.name] += 1

        obj0 = self.MODEL_CLASS.objects.create()
        update_empties(obj0)

        null_qry = self.MODEL_CLASS.objects.filter(small_pos__isnull=True)
        self.assertEqual(null_qry.count(), 1)
        self.assertEqual(null_qry.first(), obj0)
        self.assertIsNone(null_qry.first().small_pos)

        for field in [
            field.name for field in fields
            if isinstance(field, FlagField) and
            not isinstance(field, ExtraBigIntegerFlagField)
        ]:
            EnumClass = self.MODEL_CLASS._meta.get_field(field).enum

            empty = self.MODEL_CLASS.objects.create(**{field: EnumClass(0)})
            update_empties(empty)

            # Create the model
            obj = self.MODEL_CLASS.objects.create(**{field: EnumClass.ONE})
            update_empties(obj)
    
            # does this work in SQLite?
            self.MODEL_CLASS.objects.filter(pk=obj.pk).update(**{
                field: F(field).bitor(
                    EnumClass.TWO
                )
            })
    
            # Set flags manually
            self.MODEL_CLASS.objects.filter(pk=obj.pk).update(**{
                field: (
                    EnumClass.ONE |
                    EnumClass.THREE |
                    EnumClass.FOUR
                )
            })
    
            # Remove THREE (does not work in SQLite)
            self.MODEL_CLASS.objects.filter(pk=obj.pk).update(**{
                field: F(field).bitand(
                    invert_flags(EnumClass.THREE)
                )
            })
    
            # Find by awesome_flag
            fltr = self.MODEL_CLASS.objects.filter(**{
                field: (
                    EnumClass.ONE | EnumClass.FOUR
                )
            })
            try:
                self.assertEqual(fltr.count(), 1)
            except:
                import ipdb
                ipdb.set_trace()
            self.assertEqual(fltr.first().pk, obj.pk)
            self.assertEqual(
                getattr(fltr.first(), field),
                EnumClass.ONE | EnumClass.FOUR
            )
    
            if sys.version_info >= (3, 11):
                not_other = invert_flags(EnumClass.ONE | EnumClass.FOUR)
            else:
                not_other = EnumClass.TWO | EnumClass.THREE | EnumClass.FIVE
    
            fltr2 = self.MODEL_CLASS.objects.filter(**{
                field: not_other
            })
            self.assertEqual(fltr2.count(), 0)
    
            obj2 = self.MODEL_CLASS.objects.create(**{
                field: not_other
            })
            update_empties(obj2)
            self.assertEqual(fltr2.count(), 1)
            self.assertEqual(fltr2.first().pk, obj2.pk)
            self.assertEqual(
                getattr(fltr2.first(), field),
                not_other
            )
    
            obj3 = self.MODEL_CLASS.objects.create(**{
                field: EnumClass.ONE | EnumClass.TWO,
            })
            update_empties(obj3)
    
            for cont in [
                self.MODEL_CLASS.objects.filter(**{
                    f'{field}__has_any': EnumClass.ONE
                }),
                self.MODEL_CLASS.objects.filter(**{
                    f'{field}__has_all': EnumClass.ONE
                })
            ]:
                self.assertEqual(cont.count(), 2)
                self.assertIn(obj3, cont)
                self.assertIn(obj, cont)
                self.assertNotIn(obj2, cont)
    
            cont2 = self.MODEL_CLASS.objects.filter(**{
                f'{field}__has_any': (
                    EnumClass.ONE | EnumClass.TWO
                )
            })
            self.assertEqual(cont2.count(), 3)
            self.assertIn(obj3, cont2)
            self.assertIn(obj2, cont2)
            self.assertIn(obj, cont2)
    
            cont3 = self.MODEL_CLASS.objects.filter(**{
                f'{field}__has_all': (
                    EnumClass.ONE | EnumClass.TWO
                )
            })
            self.assertEqual(cont3.count(), 1)
            self.assertIn(obj3, cont3)
    
            cont4 = self.MODEL_CLASS.objects.filter(**{
                f'{field}__has_all': (
                    EnumClass.THREE | EnumClass.FIVE
                )
            })
            self.assertEqual(cont4.count(), 1)
            self.assertIn(obj2, cont4)
    
            cont5 = self.MODEL_CLASS.objects.filter(**{
                f'{field}__has_all': (
                    EnumClass.ONE | EnumClass.FIVE
                )
            })
            self.assertEqual(cont5.count(), 0)
    
            cont6 = self.MODEL_CLASS.objects.filter(**{
                f'{field}__has_any': (
                    EnumClass.FOUR | EnumClass.FIVE
                )
            })
            self.assertEqual(cont6.count(), 2)
            self.assertIn(obj, cont6)
            self.assertIn(obj2, cont6)
    
            cont7 = self.MODEL_CLASS.objects.filter(**{
                f'{field}__has_any': EnumClass(0)
            })
            self.assertEqual(cont7.count(), empties[field])
            self.assertIn(empty, cont7)
    
            cont8 = self.MODEL_CLASS.objects.filter(**{
                f'{field}__has_all': EnumClass(0)
            })
            self.assertEqual(cont8.count(), empties[field])
            self.assertIn(empty, cont8)
    
            cont9 = self.MODEL_CLASS.objects.filter(**{
                field: EnumClass(0)
            })
            self.assertEqual(cont9.count(), empties[field])
            self.assertIn(empty, cont9)
    
            cont10 = self.MODEL_CLASS.objects.filter(**{
                f'{field}__exact': EnumClass(0)
            })
            self.assertEqual(cont10.count(), empties[field])
            self.assertIn(empty, cont10)

        EnumClass = self.MODEL_CLASS._meta.get_field('pos').enum
        compound_qry = self.MODEL_CLASS.objects.filter(
            Q(small_pos__isnull=True) | Q(pos__has_any=EnumClass.ONE)
        )

        self.assertEqual(compound_qry.count(), 9)
        for obj in compound_qry:
            self.assertTrue(obj.small_pos is None or obj.pos & EnumClass.ONE)

        compound_qry = self.MODEL_CLASS.objects.filter(
            Q(small_pos__isnull=True) & Q(pos__has_any=EnumClass.ONE)
        )
        self.assertEqual(compound_qry.count(), 2)
        for obj in compound_qry:
            self.assertTrue(obj.small_pos is None and obj.pos & EnumClass.ONE)

    def test_unsupported_flags(self):
        obj = self.MODEL_CLASS.objects.create()
        for field in [
            'small_neg', 'neg', 'big_neg', 'extra_big_neg', 'extra_big_pos'
        ]:
            EnumClass = self.MODEL_CLASS._meta.get_field(field).enum
            with self.assertRaises(FieldError):
                self.MODEL_CLASS.objects.filter(
                    **{'field__has_any': EnumClass.ONE}
                )

            with self.assertRaises(FieldError):
                self.MODEL_CLASS.objects.filter(
                    **{'field__has_all': EnumClass.ONE}
                )

if ENUM_PROPERTIES_INSTALLED:

    from django_enum.forms import EnumChoiceField
    from django_enum.tests.enum_prop.enums import (
        GNSSConstellation,
        LargeBitField,
        LargeNegativeField,
        PrecedenceTest,
    )
    from django_enum.tests.enum_prop.forms import EnumTesterForm
    from django_enum.tests.enum_prop.models import (
        BitFieldModel,
        EnumFlagPropTester,
        EnumTester,
        MyModel,
    )
    from enum_properties import s


    class TestEnumPropertiesIntegration(EnumTypeMixin, TestCase):

        MODEL_CLASS = EnumTester

        def test_properties_and_symmetry(self):
            self.assertEqual(self.Constants.PI.symbol, 'π')
            self.assertEqual(self.Constants.e.symbol, 'e')
            self.assertEqual(self.Constants.GOLDEN_RATIO.symbol, 'φ')

            # test symmetry
            self.assertEqual(self.Constants.PI, self.Constants('π'))
            self.assertEqual(self.Constants.e, self.Constants('e'))
            self.assertEqual(self.Constants.GOLDEN_RATIO, self.Constants('φ'))

            self.assertEqual(self.Constants.PI, self.Constants('PI'))
            self.assertEqual(self.Constants.e, self.Constants('e'))
            self.assertEqual(self.Constants.GOLDEN_RATIO, self.Constants('GOLDEN_RATIO'))

            self.assertEqual(self.Constants.PI, self.Constants('Pi'))
            self.assertEqual(self.Constants.e, self.Constants("Euler's Number"))
            self.assertEqual(self.Constants.GOLDEN_RATIO, self.Constants('Golden Ratio'))

            self.assertEqual(self.TextEnum.VALUE1.version, 0)
            self.assertEqual(self.TextEnum.VALUE2.version, 1)
            self.assertEqual(self.TextEnum.VALUE3.version, 2)
            self.assertEqual(self.TextEnum.DEFAULT.version, 3)

            self.assertEqual(self.TextEnum.VALUE1.help,
                             'Some help text about value1.')
            self.assertEqual(self.TextEnum.VALUE2.help,
                             'Some help text about value2.')
            self.assertEqual(self.TextEnum.VALUE3.help,
                             'Some help text about value3.')
            self.assertEqual(self.TextEnum.DEFAULT.help,
                             'Some help text about default.')

            self.assertEqual(self.TextEnum.VALUE1, self.TextEnum('VALUE1'))
            self.assertEqual(self.TextEnum.VALUE2, self.TextEnum('VALUE2'))
            self.assertEqual(self.TextEnum.VALUE3, self.TextEnum('VALUE3'))
            self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum('DEFAULT'))

            self.assertEqual(self.TextEnum.VALUE1, self.TextEnum('Value1'))
            self.assertEqual(self.TextEnum.VALUE2, self.TextEnum('Value2'))
            self.assertEqual(self.TextEnum.VALUE3, self.TextEnum('Value3'))
            self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum('Default'))

            # test asymmetry
            self.assertRaises(ValueError, self.TextEnum, 0)
            self.assertRaises(ValueError, self.TextEnum, 1)
            self.assertRaises(ValueError, self.TextEnum, 2)
            self.assertRaises(ValueError, self.TextEnum, 3)

            # test asymmetry
            self.assertRaises(ValueError, self.TextEnum,
                              'Some help text about value1.')
            self.assertRaises(ValueError, self.TextEnum,
                              'Some help text about value2.')
            self.assertRaises(ValueError, self.TextEnum,
                              'Some help text about value3.')
            self.assertRaises(ValueError, self.TextEnum,
                              'Some help text about default.')

            # test basic case insensitive iterable symmetry
            self.assertEqual(self.TextEnum.VALUE1, self.TextEnum('val1'))
            self.assertEqual(self.TextEnum.VALUE1, self.TextEnum('v1'))
            self.assertEqual(self.TextEnum.VALUE1, self.TextEnum('v one'))
            self.assertEqual(self.TextEnum.VALUE1, self.TextEnum('VaL1'))
            self.assertEqual(self.TextEnum.VALUE1, self.TextEnum('V1'))
            self.assertEqual(self.TextEnum.VALUE1, self.TextEnum('v ONE'))

            self.assertEqual(self.TextEnum.VALUE2, self.TextEnum('val22'))
            self.assertEqual(self.TextEnum.VALUE2, self.TextEnum('v2'))
            self.assertEqual(self.TextEnum.VALUE2, self.TextEnum('v two'))
            self.assertEqual(self.TextEnum.VALUE2, self.TextEnum('VaL22'))
            self.assertEqual(self.TextEnum.VALUE2, self.TextEnum('V2'))
            self.assertEqual(self.TextEnum.VALUE2, self.TextEnum('v TWo'))

            self.assertEqual(self.TextEnum.VALUE3, self.TextEnum('val333'))
            self.assertEqual(self.TextEnum.VALUE3, self.TextEnum('v3'))
            self.assertEqual(self.TextEnum.VALUE3, self.TextEnum('v three'))
            self.assertEqual(self.TextEnum.VALUE3, self.TextEnum('VaL333'))
            self.assertEqual(self.TextEnum.VALUE3, self.TextEnum('V333'))
            self.assertEqual(self.TextEnum.VALUE3, self.TextEnum('v THRee'))

            self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum('default'))
            self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum('DeFaULT'))
            self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum('DEfacTO'))
            self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum('defacto'))
            self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum('NONE'))
            self.assertEqual(self.TextEnum.DEFAULT, self.TextEnum('none'))

        def test_value_type_coercion(self):
            """test basic value coercion from str"""
            self.assertEqual(self.Constants.PI, self.Constants(
                '3.14159265358979323846264338327950288'))
            self.assertEqual(self.Constants.e, self.Constants('2.71828'))
            self.assertEqual(self.Constants.GOLDEN_RATIO, self.Constants(
                '1.61803398874989484820458683436563811'))

            self.assertEqual(self.SmallPosIntEnum.VAL1, self.SmallPosIntEnum('0'))
            self.assertEqual(self.SmallPosIntEnum.VAL2, self.SmallPosIntEnum('2'))
            self.assertEqual(self.SmallPosIntEnum.VAL3, self.SmallPosIntEnum('32767'))

            self.assertEqual(self.SmallIntEnum.VALn1, self.SmallIntEnum('-32768'))
            self.assertEqual(self.SmallIntEnum.VAL0, self.SmallIntEnum('0'))
            self.assertEqual(self.SmallIntEnum.VAL1, self.SmallIntEnum('1'))
            self.assertEqual(self.SmallIntEnum.VAL2, self.SmallIntEnum('2'))
            self.assertEqual(self.SmallIntEnum.VAL3, self.SmallIntEnum('32767'))

            self.assertEqual(self.IntEnum.VALn1, self.IntEnum('-2147483648'))
            self.assertEqual(self.IntEnum.VAL0, self.IntEnum('0'))
            self.assertEqual(self.IntEnum.VAL1, self.IntEnum('1'))
            self.assertEqual(self.IntEnum.VAL2, self.IntEnum('2'))
            self.assertEqual(self.IntEnum.VAL3, self.IntEnum('2147483647'))

            self.assertEqual(self.PosIntEnum.VAL0, self.PosIntEnum('0'))
            self.assertEqual(self.PosIntEnum.VAL1, self.PosIntEnum('1'))
            self.assertEqual(self.PosIntEnum.VAL2, self.PosIntEnum('2'))
            self.assertEqual(self.PosIntEnum.VAL3, self.PosIntEnum('2147483647'))

            self.assertEqual(self.BigPosIntEnum.VAL0, self.BigPosIntEnum('0'))
            self.assertEqual(self.BigPosIntEnum.VAL1, self.BigPosIntEnum('1'))
            self.assertEqual(self.BigPosIntEnum.VAL2, self.BigPosIntEnum('2'))
            self.assertEqual(self.BigPosIntEnum.VAL3, self.BigPosIntEnum('2147483648'))

            self.assertEqual(self.BigIntEnum.VAL0, self.BigIntEnum('-2147483649'))
            self.assertEqual(self.BigIntEnum.VAL1, self.BigIntEnum('1'))
            self.assertEqual(self.BigIntEnum.VAL2, self.BigIntEnum('2'))
            self.assertEqual(self.BigIntEnum.VAL3, self.BigIntEnum('2147483648'))

        def test_symmetric_type_coercion(self):
            """test that symmetric properties have types coerced"""
            self.assertEqual(self.BigIntEnum.VAL0, self.BigIntEnum(self.BigPosIntEnum.VAL0))
            self.assertEqual(self.BigIntEnum.VAL1, self.BigIntEnum(self.BigPosIntEnum.VAL1))
            self.assertEqual(self.BigIntEnum.VAL2, self.BigIntEnum(self.BigPosIntEnum.VAL2))
            self.assertEqual(self.BigIntEnum.VAL3, self.BigIntEnum(self.BigPosIntEnum.VAL3))

            self.assertEqual(self.BigIntEnum.VAL0, self.BigIntEnum(0))
            self.assertEqual(self.BigIntEnum.VAL0, self.BigIntEnum('0'))

        def test_no_labels(self):
            """
            Tests that an enum without labels and with properties works as expected
            """

            class NoLabels(TextChoices, s('not_a_label')):
                VAL1 = 'E1', 'E1 Label'
                VAL2 = 'E2', 'E2 Label'

            self.assertEqual(NoLabels.VAL1.label, 'VAL1'.title())
            self.assertEqual(NoLabels.VAL1.name, 'VAL1')
            self.assertEqual(NoLabels.VAL2.label, 'VAL2'.title())
            self.assertEqual(NoLabels.VAL2.name, 'VAL2')
            self.assertEqual(NoLabels.VAL1.not_a_label, 'E1 Label')
            self.assertEqual(NoLabels.VAL2.not_a_label, 'E2 Label')

            self.assertEqual(NoLabels.VAL1, NoLabels('E1 Label'))
            self.assertEqual(NoLabels.VAL2, NoLabels('E2 Label'))

            self.assertEqual(NoLabels.VAL1, NoLabels('VAL1'))
            self.assertEqual(NoLabels.VAL1, NoLabels('Val1'))

            self.assertEqual(NoLabels.VAL1, NoLabels('E1'))
            self.assertEqual(NoLabels.VAL2, NoLabels('E2'))

            class NoLabelsOrProps(TextChoices):
                VAL1 = 'E1'
                VAL2 = 'E2'

            self.assertEqual(NoLabelsOrProps.VAL1.label, 'VAL1'.title())
            self.assertEqual(NoLabelsOrProps.VAL1.name, 'VAL1')
            self.assertEqual(NoLabelsOrProps.VAL2.label, 'VAL2'.title())
            self.assertEqual(NoLabelsOrProps.VAL2.name, 'VAL2')

            self.assertEqual(NoLabelsOrProps.VAL1, NoLabelsOrProps('VAL1'))
            self.assertEqual(NoLabelsOrProps.VAL2, NoLabelsOrProps('Val2'))

            self.assertEqual(NoLabelsOrProps.VAL1, NoLabelsOrProps('E1'))
            self.assertEqual(NoLabelsOrProps.VAL2, NoLabelsOrProps('E2'))

        def test_saving(self):
            """
            Test that enum values can be saved directly.
            """
            tester = self.MODEL_CLASS.objects.create(
                small_pos_int=self.SmallPosIntEnum.VAL2,
                small_int=self.SmallIntEnum.VAL0,
                pos_int=self.PosIntEnum.VAL1,
                int=self.IntEnum.VALn1,
                big_pos_int=self.BigPosIntEnum.VAL3,
                big_int=self.BigIntEnum.VAL2,
                date_enum=self.DateEnum.BRIAN,
                datetime_enum=self.DateTimeEnum.PINATUBO,
                duration_enum=self.DurationEnum.FORTNIGHT,
                time_enum=self.TimeEnum.LUNCH,
                decimal_enum=self.DecimalEnum.THREE,
                constant=self.Constants.GOLDEN_RATIO,
                text=self.TextEnum.VALUE2,
                extern=self.ExternEnum.ONE
            )

            self.assertEqual(tester.small_pos_int, self.SmallPosIntEnum.VAL2)
            self.assertEqual(tester.small_int, self.SmallIntEnum.VAL0)
            self.assertEqual(tester.pos_int, self.PosIntEnum.VAL1)
            self.assertEqual(tester.int, self.IntEnum.VALn1)
            self.assertEqual(tester.big_pos_int, self.BigPosIntEnum.VAL3)
            self.assertEqual(tester.big_int, self.BigIntEnum.VAL2)
            self.assertEqual(tester.constant, self.Constants.GOLDEN_RATIO)
            self.assertEqual(tester.text, self.TextEnum.VALUE2)
            self.assertEqual(tester.extern, self.ExternEnum.ONE)
            self.assertEqual(tester.date_enum, self.DateEnum.BRIAN)
            self.assertEqual(tester.datetime_enum, self.DateTimeEnum.PINATUBO)
            self.assertEqual(tester.duration_enum, self.DurationEnum.FORTNIGHT)
            self.assertEqual(tester.time_enum, self.TimeEnum.LUNCH)
            self.assertEqual(tester.decimal_enum, self.DecimalEnum.THREE)

            tester.small_pos_int = self.SmallPosIntEnum.VAL1
            tester.small_int = self.SmallIntEnum.VAL2
            tester.pos_int = self.PosIntEnum.VAL0
            tester.int = self.IntEnum.VAL1
            tester.big_pos_int = self.BigPosIntEnum.VAL2
            tester.big_int = self.BigIntEnum.VAL1
            tester.constant = self.Constants.PI
            tester.text = self.TextEnum.VALUE3
            tester.extern = self.ExternEnum.TWO

            tester.save()

            self.assertEqual(tester.small_pos_int, self.SmallPosIntEnum.VAL1)
            self.assertEqual(tester.small_int, self.SmallIntEnum.VAL2)
            self.assertEqual(tester.pos_int, self.PosIntEnum.VAL0)
            self.assertEqual(tester.int, self.IntEnum.VAL1)
            self.assertEqual(tester.big_pos_int, self.BigPosIntEnum.VAL2)
            self.assertEqual(tester.big_int, self.BigIntEnum.VAL1)
            self.assertEqual(tester.constant, self.Constants.PI)
            self.assertEqual(tester.text, self.TextEnum.VALUE3)
            self.assertEqual(tester.extern, self.ExternEnum.TWO)

            tester.refresh_from_db()

            self.assertEqual(tester.small_pos_int, self.SmallPosIntEnum.VAL1)
            self.assertEqual(tester.small_int, self.SmallIntEnum.VAL2)
            self.assertEqual(tester.pos_int, self.PosIntEnum.VAL0)
            self.assertEqual(tester.int, self.IntEnum.VAL1)
            self.assertEqual(tester.big_pos_int, self.BigPosIntEnum.VAL2)
            self.assertEqual(tester.big_int, self.BigIntEnum.VAL1)
            self.assertEqual(tester.constant, self.Constants.PI)
            self.assertEqual(tester.text, self.TextEnum.VALUE3)
            self.assertEqual(tester.extern, self.ExternEnum.TWO)

            tester.small_pos_int = '32767'
            tester.small_int = -32768
            tester.pos_int = 2147483647
            tester.int = -2147483648
            tester.big_pos_int = 2147483648
            tester.big_int = -2147483649
            tester.constant = '2.71828'
            tester.text = 'D'
            tester.extern = 'Three'

            tester.save()
            tester.refresh_from_db()

            self.assertEqual(tester.small_pos_int, 32767)
            self.assertEqual(tester.small_int, -32768)
            self.assertEqual(tester.pos_int, 2147483647)
            self.assertEqual(tester.int, -2147483648)
            self.assertEqual(tester.big_pos_int, 2147483648)
            self.assertEqual(tester.big_int, -2147483649)
            self.assertEqual(tester.constant, 2.71828)
            self.assertEqual(tester.text, 'D')
            self.assertEqual(tester.extern, self.ExternEnum.THREE)

            with transaction.atomic():
                tester.text = 'not valid'
                self.assertRaises(ValueError, tester.save)
            tester.refresh_from_db()

            with transaction.atomic():
                tester.text = type('WrongType')()
                self.assertRaises(ValueError, tester.save)
            tester.refresh_from_db()

            with transaction.atomic():
                tester.text = 1
                self.assertRaises(ValueError, tester.save)
            tester.refresh_from_db()

            # fields with choices are more permissive - choice check does not happen on basic save
            with transaction.atomic():
                tester.char_choice = 'not valid'
                tester.save()
                # self.assertRaises(ValidationError, tester.save)
            tester.refresh_from_db()

            with transaction.atomic():
                tester.char_choice = 5
                tester.save()
                # self.assertRaises(ValueError, tester.save)
            tester.refresh_from_db()

            with transaction.atomic():
                tester.int_choice = 5
                tester.save()
                # self.assertRaises(ValueError, tester.save)
            tester.refresh_from_db()
            #####################################################################################

            with transaction.atomic():
                tester.int_choice = 'a'
                self.assertRaises(ValueError, tester.save)
            tester.refresh_from_db()

            tester.text = None
            tester.save()
            self.assertEqual(tester.text, None)


    class TestSymmetricEmptyValEquivalency(TestCase):

        def test(self):

            class EmptyEqEnum(TextChoices, s('prop', case_fold=True)):

                A = 'A', 'ok'
                B = 'B', 'none'

            form_field = EnumChoiceField(enum=EmptyEqEnum)
            self.assertTrue(None in form_field.empty_values)

            class EmptyEqEnum(TextChoices, s('prop', case_fold=True)):

                A = 'A', 'ok'
                B = 'B', None

            form_field = EnumChoiceField(enum=EmptyEqEnum)
            self.assertTrue(None in form_field.empty_values)

            class EmptyEqEnum(TextChoices, s('prop', match_none=True)):

                A = 'A', 'ok'
                B = 'B', None

            form_field = EnumChoiceField(enum=EmptyEqEnum)
            self.assertTrue(None not in form_field.empty_values)

            # version 1.5.0 of enum_properties changed the default symmetricity
            # of none values.
            from enum_properties import VERSION
            match_none = {} if VERSION < (1, 5, 0) else {'match_none': True}
            
            class EmptyEqEnum2(
                TextChoices,
                s('prop', case_fold=True, **match_none)
            ):

                A = 'A', [None, '', ()]
                B = 'B', 'ok'

            field = EnumChoiceField(enum=EmptyEqEnum2, empty_values=[None, '', ()])
            self.assertEqual(field.empty_values, [None, '', ()])
            self.assertEqual(field.empty_value, '')

            field2 = EnumChoiceField(enum=EmptyEqEnum2, empty_value=0)
            self.assertEqual(field2.empty_values, [0, [], {}])
            self.assertEqual(field2.empty_value, 0)

            field3 = EnumChoiceField(enum=EmptyEqEnum2, empty_values=[None, ()])
            self.assertEqual(field3.empty_values, [None, ()])
            self.assertEqual(field3.empty_value, None)

            self.assertRaises(
                ValueError,
                EnumChoiceField,
                enum=EmptyEqEnum2,
                empty_value=0,
                empty_values=[None, '', ()]
            )

            try:
                class EmptyEqEnum2(TextChoices, s('prop', case_fold=True)):
                    A = 'A', [None, '', ()]
                    B = 'B', 'ok'

                EnumChoiceField(
                    enum=EmptyEqEnum2,
                    empty_value=0,
                    empty_values=[0, None, '', ()]
                )
            except Exception:  # pragma: no cover
                self.fail(
                    "EnumChoiceField() raised value error with alternative"
                    "empty_value set."
                )


    class TestFieldTypeResolutionProps(TestFieldTypeResolution):
        MODEL_CLASS = EnumTester

        def test_large_bitfields(self):

            tester = BitFieldModel.objects.create(
                bit_field_small=GNSSConstellation.GPS | GNSSConstellation.GLONASS
            )
            from django.db.models import BinaryField, PositiveSmallIntegerField
            self.assertIsInstance(tester._meta.get_field('bit_field_small'), PositiveSmallIntegerField)
            self.assertIsInstance(tester._meta.get_field('bit_field_large'), BinaryField)
            self.assertIsInstance(tester._meta.get_field('bit_field_large_neg'), BinaryField)

            self.assertEqual(tester.bit_field_small, GNSSConstellation.GPS | GNSSConstellation.GLONASS)
            self.assertEqual(tester.bit_field_large, None)
            self.assertEqual(tester.bit_field_large_neg, LargeNegativeField.NEG_ONE)
            self.assertEqual(tester.no_default, LargeBitField(0))

            self.assertEqual(
                BitFieldModel.objects.filter(bit_field_large__isnull=True).count(),
                1
            )
            tester.bit_field_large = LargeBitField.ONE | LargeBitField.TWO
            tester.save()
            self.assertEqual(
                BitFieldModel.objects.filter(bit_field_large__isnull=True).count(),
                0
            )
            self.assertEqual(
                BitFieldModel.objects.filter(bit_field_large=LargeBitField.ONE | LargeBitField.TWO).count(),
                1
            )
            self.assertEqual(
                BitFieldModel.objects.filter(bit_field_large=LargeBitField.ONE).count(),
                0
            )

            # todo this breaks on sqlite, integer overflow - what about other backends?
            # BitFieldModel.objects.filter(bit_field_large=LargeBitField.ONE | LargeBitField.TWO).update(bit_field_large=F('bit_field_large').bitand(~LargeBitField.TWO))

            BitFieldModel.objects.filter(
                bit_field_large=LargeBitField.ONE | LargeBitField.TWO).update(
                bit_field_large=LargeBitField.ONE & ~LargeBitField.TWO
            )

            self.assertEqual(
                BitFieldModel.objects.filter(bit_field_large=LargeBitField.ONE).count(),
                1
            )

            self.assertEqual(
                BitFieldModel.objects.filter(bit_field_small=GNSSConstellation.GPS | GNSSConstellation.GLONASS).count(),
                1
            )

            BitFieldModel.objects.filter(
                bit_field_small=GNSSConstellation.GPS | GNSSConstellation.GLONASS
                ).update(bit_field_small=F('bit_field_small').bitand(~GNSSConstellation.GLONASS)
            )

            self.assertEqual(
                BitFieldModel.objects.filter(bit_field_small=GNSSConstellation.GPS | GNSSConstellation.GLONASS).count(),
                0
            )

            self.assertEqual(
                BitFieldModel.objects.filter(bit_field_small=GNSSConstellation.GPS).count(),
                1
            )

            tester2 = BitFieldModel.objects.create(
                bit_field_small=GNSSConstellation.GPS | GNSSConstellation.GLONASS,
                bit_field_large=LargeBitField.ONE | LargeBitField.TWO,
                bit_field_large_neg=None
            )

            # has_any and has_all are not supported on ExtraLarge bit fields
            with self.assertRaises(FieldError):
                BitFieldModel.objects.filter(bit_field_large__has_any=LargeBitField.ONE)

            with self.assertRaises(FieldError):
                BitFieldModel.objects.filter(bit_field_large__has_all=LargeBitField.ONE | LargeBitField.TWO)

            with self.assertRaises(FieldError):
                BitFieldModel.objects.filter(bit_field_large_neg__has_any=LargeNegativeField.NEG_ONE)

            with self.assertRaises(FieldError):
                BitFieldModel.objects.filter(bit_field_large_neg__has_all=LargeNegativeField.NEG_ONE | LargeNegativeField.ZERO)


    class TestEnumQueriesProps(TestEnumQueries):

        MODEL_CLASS = EnumTester

        def test_query(self):
            # don't call super b/c referenced types are different

            self.assertEqual(self.MODEL_CLASS.objects.filter(small_pos_int=self.SmallPosIntEnum.VAL2).count(), 2)
            self.assertEqual(self.MODEL_CLASS.objects.filter(small_pos_int=self.SmallPosIntEnum.VAL2.value).count(), 2)
            self.assertEqual(self.MODEL_CLASS.objects.filter(small_pos_int='Value 2').count(), 2)
            self.assertEqual(self.MODEL_CLASS.objects.filter(small_pos_int=self.SmallPosIntEnum.VAL2.name).count(), 2)

            self.assertEqual(self.MODEL_CLASS.objects.filter(big_pos_int=self.BigPosIntEnum.VAL3).count(), 2)
            self.assertEqual(self.MODEL_CLASS.objects.filter(big_pos_int=self.BigPosIntEnum.VAL3.label).count(), 2)
            self.assertEqual(self.MODEL_CLASS.objects.filter(big_pos_int=None).count(), 1)

            self.assertEqual(self.MODEL_CLASS.objects.filter(constant=self.Constants.GOLDEN_RATIO).count(), 2)
            self.assertEqual(self.MODEL_CLASS.objects.filter(constant=self.Constants.GOLDEN_RATIO.name).count(), 2)
            self.assertEqual(self.MODEL_CLASS.objects.filter(constant=self.Constants.GOLDEN_RATIO.value).count(), 2)
            self.assertEqual(self.MODEL_CLASS.objects.filter(constant__isnull=True).count(), 1)

            # test symmetry
            self.assertEqual(self.MODEL_CLASS.objects.filter(constant=self.Constants.GOLDEN_RATIO.symbol).count(), 2)
            self.assertEqual(self.MODEL_CLASS.objects.filter(constant='φ').count(), 2)

            self.assertEqual(self.MODEL_CLASS.objects.filter(text=self.TextEnum.VALUE2).count(), 2)
            self.assertEqual(len(self.TextEnum.VALUE2.aliases), 3)
            for alias in self.TextEnum.VALUE2.aliases:
                self.assertEqual(self.MODEL_CLASS.objects.filter(text=alias).count(), 2)

            self.assertEqual(self.MODEL_CLASS.objects.filter(extern='One').count(), 2)
            self.assertEqual(self.MODEL_CLASS.objects.filter(extern='Two').count(), 0)

            self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, int_field='a')
            self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, float_field='a')
            self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, constant='p')
            self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, big_pos_int='p')
            self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, big_pos_int=type('WrongType')())


    class PrecedenceTestCase(TestCase):

        def test_precedence(self):
            """
            test that symmetric properties with non-hashable iterable values treat each iterable as a separate
            symmetric value
            """
            self.assertEqual(PrecedenceTest.P1, PrecedenceTest(0))
            self.assertEqual(PrecedenceTest.P2, PrecedenceTest(1))
            self.assertEqual(PrecedenceTest.P3, PrecedenceTest(2))
            self.assertEqual(PrecedenceTest.P4, PrecedenceTest(3))

            self.assertEqual(PrecedenceTest.P1, PrecedenceTest('Precedence 1'))
            self.assertEqual(PrecedenceTest.P2, PrecedenceTest('Precedence 2'))
            self.assertEqual(PrecedenceTest.P3, PrecedenceTest('Precedence 3'))
            self.assertEqual(PrecedenceTest.P4, PrecedenceTest('Precedence 4'))

            # type match takes precedence
            self.assertEqual(PrecedenceTest.P3, PrecedenceTest('1'))
            self.assertEqual(PrecedenceTest.P1, PrecedenceTest('0.4'))
            self.assertEqual(PrecedenceTest.P2, PrecedenceTest('0.3'))

            self.assertEqual(PrecedenceTest.P1, PrecedenceTest(0.1))
            self.assertEqual(PrecedenceTest.P2, PrecedenceTest(0.2))
            self.assertEqual(PrecedenceTest.P1, PrecedenceTest('0.1'))
            self.assertEqual(PrecedenceTest.P2, PrecedenceTest('0.2'))
            self.assertEqual(PrecedenceTest.P3, PrecedenceTest(0.3))
            self.assertEqual(PrecedenceTest.P4, PrecedenceTest(0.4))

            self.assertEqual(PrecedenceTest.P1, PrecedenceTest('First'))
            self.assertEqual(PrecedenceTest.P2, PrecedenceTest('Second'))
            self.assertEqual(PrecedenceTest.P3, PrecedenceTest('Third'))
            self.assertEqual(PrecedenceTest.P4, PrecedenceTest('Fourth'))

            # lower priority case insensitive match
            self.assertEqual(PrecedenceTest.P4, PrecedenceTest('FIRST'))
            self.assertEqual(PrecedenceTest.P3, PrecedenceTest('SECOND'))
            self.assertEqual(PrecedenceTest.P2, PrecedenceTest('THIRD'))
            self.assertEqual(PrecedenceTest.P1, PrecedenceTest('FOURTH'))

            self.assertEqual(PrecedenceTest.P4, PrecedenceTest(4))
            self.assertEqual(PrecedenceTest.P4, PrecedenceTest('4'))


    class TestBulkOperationsProps(TestBulkOperations):
        MODEL_CLASS = EnumTester

        @property
        def create_params(self):
            return {
                'small_pos_int': self.SmallPosIntEnum.VAL2,
                'small_int': 'Value -32768',
                'pos_int': 2147483647,
                'int': -2147483648,
                'big_pos_int': 'Value 2147483648',
                'big_int': 'VAL2',
                'constant': 'φ',
                'text': 'V TWo',
                'extern': 'One',
                'dj_int_enum': 3,
                'dj_text_enum': self.DJTextEnum.A,
                'non_strict_int': 15,
                'non_strict_text': 'arbitrary',
                'no_coerce': 'Value 2'
            }

        @property
        def update_params(self):
            return {
                'non_strict_int': 100,
                'non_strict_text': self.TextEnum.VALUE3,
                'constant': 'π',
                'big_int': -2147483649,
                'coerce': 2
            }


    class TestFormFieldSymmetric(TestFormField):

        MODEL_CLASS = EnumTester
        FORM_CLASS = EnumTesterForm
        form_type = None

        @property
        def model_params(self):
            return {
                'small_pos_int': 0,
                'small_int': self.SmallIntEnum.VAL2,
                'pos_int': 'Value 2147483647',
                'int': 'VALn1',
                'big_pos_int': 2,
                'big_int': self.BigPosIntEnum.VAL2,
                'constant': 'π',
                'text': 'none',
                'extern': 'three',
                'dj_int_enum': 2,
                'dj_text_enum': 'B',
                'non_strict_int': 1,
                'non_strict_text': 'arbitrary',
                'no_coerce': 'Value 1'
            }

    class TestRequestsProps(TestRequests):
        MODEL_CLASS = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'

        @property
        def post_params(self):
            return {
                'small_pos_int': self.SmallPosIntEnum.VAL2,
                'small_int': self.SmallIntEnum.VAL0,
                'pos_int': self.PosIntEnum.VAL1,
                'int': self.IntEnum.VALn1,
                'big_pos_int': self.BigPosIntEnum.VAL3,
                'big_int': self.BigIntEnum.VAL2,
                'date_enum': self.DateEnum.BRIAN.value,
                'datetime_enum': self.DateTimeEnum.PINATUBO.value,
                'duration_enum': self.DurationEnum.FORTNIGHT.value,
                'time_enum': self.TimeEnum.LUNCH.value,
                'decimal_enum': self.DecimalEnum.THREE.value,
                'constant': self.Constants.GOLDEN_RATIO,
                'text': self.TextEnum.VALUE2,
                'extern': self.ExternEnum.TWO,
                'dj_int_enum': self.DJIntEnum.TWO,
                'dj_text_enum': self.DJTextEnum.C,
                'non_strict_int': self.SmallPosIntEnum.VAL1,
                'non_strict_text': self.TextEnum.VALUE2,
                'no_coerce': self.SmallPosIntEnum.VAL3
            }

        @property
        def post_params_symmetric(self):
            return {
                'small_pos_int': self.SmallPosIntEnum.VAL2,
                'small_int': 'Value 0',
                'pos_int': self.PosIntEnum.VAL1,
                'int': -2147483648,
                'big_pos_int': self.BigPosIntEnum.VAL2,
                'big_int': self.BigPosIntEnum.VAL2,
                'date_enum': self.DateEnum.BRIAN.value,
                'datetime_enum': datetime(
                    year=1964, month=3, day=28, hour=17, minute=36, second=0
                ),
                'duration_enum': self.DurationEnum.FORTNIGHT.value,
                'time_enum': self.TimeEnum.LUNCH.value,
                'decimal_enum': self.DecimalEnum.THREE.value,
                'constant': 'φ',
                'text': 'v two',
                'extern': 'two',
                'dj_int_enum': self.DJIntEnum.TWO,
                'dj_text_enum': self.DJTextEnum.C,
                'non_strict_int': 150,
                'non_strict_text': 'arbitrary',
                'no_coerce': 'Value 32767'
            }

        @property
        def field_filter_properties(self):
            return {
                'small_pos_int': ['value', 'name', 'label'],
                'small_int': ['value', 'name', 'label'],
                'pos_int': ['value', 'name', 'label'],
                'int': ['value', 'name', 'label'],
                'big_pos_int': ['value', 'name', 'label'],
                'big_int': ['value', 'name', 'label', 'pos'],
                'constant': ['value', 'name', 'label', 'symbol'],
                'text': ['value', 'name', 'label', 'aliases'],
                'date_enum': ['value', 'name', 'label'],
                'datetime_enum': ['value', 'name', 'label'],
                'duration_enum': ['value', 'name', 'label'],
                'time_enum': ['value', 'name', 'label'],
                'decimal_enum': ['value', 'name', 'label'],
                'extern': ['value', 'name', 'label'],
                'dj_int_enum': ['value'],
                'dj_text_enum': ['value'],
                'non_strict_int': ['value', 'name', 'label'],
                'non_strict_text': ['value', 'name', 'label'],
                'no_coerce': ['value', 'name', 'label']
            }

        if DJANGO_FILTERS_INSTALLED:
            def test_django_filter(self):
                self.do_test_django_filter(
                    reverse(f'{self.NAMESPACE}:enum-filter-symmetric'),
                    skip_non_strict=False
                )
        else:
            pass  # pragma: no cover

    class TestExamples(TestCase):

        def test_readme(self):
            instance = MyModel.objects.create(
                txt_enum=MyModel.TextEnum.VALUE1,
                int_enum=3,  # by-value assignment also works
                color=MyModel.Color('FF0000')
            )

            self.assertEqual(instance.txt_enum, MyModel.TextEnum('V1'))
            self.assertEqual(instance.txt_enum.label, 'Value 1')

            self.assertEqual(instance.int_enum, MyModel.IntEnum['THREE'])

            instance.full_clean()
            self.assertEqual(instance.int_enum.value, 3)

            self.assertEqual(instance.color, MyModel.Color('Red'))
            self.assertEqual(instance.color, MyModel.Color('R'))
            self.assertEqual(instance.color, MyModel.Color((1, 0, 0)))

            # save back by any symmetric value
            instance.color = 'FF0000'
            instance.full_clean()
            instance.save()

            self.assertEqual(instance.color.hex, 'ff0000')

        """
        # Django breaks auto
        def test_auto_enum(self):
            from django_enum import IntegerChoices
            from enum import auto

            class AutoEnum(IntegerChoices):
                ONE = auto(), 'One'
                TWO = auto(), 'Two'
                THREE = auto(), 'Three'
        """

    class ResetModelsMixin:

        @classmethod
        def tearDownClass(cls):
            from django.conf import settings
            with open(
                    settings.TEST_MIGRATION_DIR.parent / 'models.py',
                    'w'
            ) as models_file:
                models_file.write('')

            super().tearDownClass()


    if not DISABLE_MIGRATION_TESTS:
        class TestMigrations(ResetModelsMixin, TestCase):
            """Run through migrations"""

            @classmethod
            def setUpClass(cls):
                import glob

                from django.conf import settings
                for migration in glob.glob(
                        f'{settings.TEST_MIGRATION_DIR}/000*py'):
                    os.remove(migration)

                super().setUpClass()

            def test_makemigrate_1(self):
                from django.conf import settings
                set_models(1)
                self.assertFalse(
                    os.path.isfile(settings.TEST_MIGRATION_DIR / '0001_initial.py')
                )

                call_command('makemigrations')

                self.assertTrue(
                    os.path.isfile(settings.TEST_MIGRATION_DIR / '0001_initial.py')
                )

                with open(settings.TEST_MIGRATION_DIR / '0001_initial.py', 'r') as inpt:
                    contents = inpt.read()
                    self.assertEqual(contents.count('AddConstraint'), 2)
                    self.assertEqual(contents.count("constraint=models.CheckConstraint(check=models.Q(('int_enum__in', [0, 1, 2]))"), 1)
                    self.assertEqual(contents.count("constraint=models.CheckConstraint(check=models.Q(('color__in', ['R', 'G', 'B', 'K']))"), 1)

            def test_makemigrate_2(self):
                import shutil

                from django.conf import settings
                set_models(2)
                self.assertFalse(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0002_alter_values.py')
                )

                call_command('makemigrations', name='alter_values')

                self.assertTrue(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0002_alter_values.py')
                )

                # replace this migration with our own that has custom data
                # migrations

                data_edit_functions = """
def migrate_enum_values(apps, schema_editor):

    MigrationTester = apps.get_model(
        "django_enum_tests_edit_tests",
        "MigrationTester"
    )
    db_alias = schema_editor.connection.alias
    for obj in MigrationTester.objects.using(db_alias).all():
        obj.int_enum = obj.int_enum + 1
        obj.save()


def revert_enum_values(apps, schema_editor):

    MigrationTester = apps.get_model(
        "django_enum_tests_edit_tests",
        "MigrationTester"
    )
    db_alias = schema_editor.connection.alias
    for obj in MigrationTester.objects.using(db_alias).all():
        obj.int_enum = obj.int_enum - 1
        obj.save()
                \n\n"""

                data_edit_operations = "        migrations.RunPython(migrate_enum_values, revert_enum_values),\n"

                new_contents = ''
                with open(settings.TEST_MIGRATION_DIR / '0002_alter_values.py', 'r') as inpt:
                    for line in inpt.readlines():
                        if "class Migration" in line:
                            new_contents += data_edit_functions
                        if "migrations.AddConstraint(" in line:
                            new_contents += data_edit_operations
                        new_contents += line

                with open(settings.TEST_MIGRATION_DIR / '0002_alter_values.py', 'w') as output:
                    output.write(new_contents)

                with open(settings.TEST_MIGRATION_DIR / '0002_alter_values.py', 'r') as inpt:
                    contents = inpt.read()
                    self.assertEqual(contents.count('RemoveConstraint'), 1)
                    self.assertEqual(contents.count('AddConstraint'), 1)
                    self.assertEqual(contents.count("constraint=models.CheckConstraint(check=models.Q(('int_enum__in', [1, 2, 3]))"), 1)

            def test_makemigrate_3(self):
                from django.conf import settings
                set_models(3)
                self.assertFalse(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0003_remove_black.py')
                )

                call_command('makemigrations', name='remove_black')

                self.assertTrue(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0003_remove_black.py')
                )

                data_edit_functions = """
def remove_color_values(apps, schema_editor):

    MigrationTester = apps.get_model(
        "django_enum_tests_edit_tests",
        "MigrationTester"
    )
    db_alias = schema_editor.connection.alias
    MigrationTester.objects.using(db_alias).filter(color='K').delete()
            
\n"""
                data_edit_operations = "        migrations.RunPython(remove_color_values, migrations.RunPython.noop),\n"

                new_contents = ''
                with open(settings.TEST_MIGRATION_DIR / '0003_remove_black.py',
                          'r') as inpt:
                    for line in inpt.readlines():
                        if "class Migration" in line:
                            new_contents += data_edit_functions
                        if "migrations.AddConstraint(" in line:
                            new_contents += data_edit_operations
                        new_contents += line

                with open(settings.TEST_MIGRATION_DIR / '0003_remove_black.py',
                          'w') as output:
                    output.write(new_contents)

                with open(settings.TEST_MIGRATION_DIR / '0003_remove_black.py', 'r') as inpt:
                    contents = inpt.read()
                    self.assertEqual(contents.count('RemoveConstraint'), 1)
                    self.assertEqual(contents.count('AddConstraint'), 1)
                    self.assertEqual(contents.count("constraint=models.CheckConstraint(check=models.Q(('color__in', ['R', 'G', 'B']))"), 1)

            def test_makemigrate_4(self):
                from django.conf import settings
                set_models(4)
                self.assertFalse(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0004_change_names.py')
                )

                call_command('makemigrations', name='change_names')

                # should not exist!
                self.assertFalse(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0004_change_names.py')
                )

            def test_makemigrate_5(self):
                from django.conf import settings
                set_models(5)
                self.assertFalse(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0004_remove_constraint.py')
                )

                call_command('makemigrations', name='remove_constraint')

                # should not exist!
                self.assertTrue(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0004_remove_constraint.py')
                )

                with open(settings.TEST_MIGRATION_DIR / '0004_remove_constraint.py', 'r') as inpt:
                    contents = inpt.read()
                    self.assertEqual(contents.count('RemoveConstraint'), 1)
                    self.assertEqual(contents.count('AddConstraint'), 0)

            def test_makemigrate_6(self):
                from django.conf import settings
                set_models(6)
                self.assertFalse(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0005_remove_int_enum.py')
                )

                call_command('makemigrations', name='remove_int_enum')

                # should not exist!
                self.assertTrue(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0005_remove_int_enum.py')
                )

            def test_makemigrate_7(self):
                from django.conf import settings
                set_models(7)
                self.assertFalse(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0006_add_int_enum.py')
                )

                call_command('makemigrations', name='add_int_enum')

                # should not exist!
                self.assertTrue(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0006_add_int_enum.py')
                )

                with open(settings.TEST_MIGRATION_DIR / '0006_add_int_enum.py', 'r') as inpt:
                    contents = inpt.read()
                    self.assertEqual(contents.count('RemoveConstraint'), 1)
                    self.assertEqual(contents.count('AddConstraint'), 2)
                    self.assertEqual(contents.count("constraint=models.CheckConstraint(check=models.Q(('int_enum__in', ['A', 'B', 'C'])"), 1)
                    self.assertEqual(contents.count("constraint=models.CheckConstraint(check=models.Q(('color__in', ['R', 'G', 'B', 'K']))"), 1)

            def test_makemigrate_8(self):
                from django.conf import settings
                set_models(8)
                self.assertFalse(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0007_set_default.py')
                )

                call_command('makemigrations', name='set_default')

                # should not exist!
                self.assertTrue(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0007_set_default.py')
                )

            def test_makemigrate_9(self):
                from django.conf import settings
                set_models(9)
                self.assertFalse(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0008_change_default.py')
                )

                call_command('makemigrations', name='change_default')

                # should not exist!
                self.assertTrue(
                    os.path.isfile(
                        settings.TEST_MIGRATION_DIR / '0008_change_default.py')
                )

        class TestInitialMigration(ResetModelsMixin, MigratorTestCase):

            migrate_from = ('django_enum_tests_edit_tests', '0001_initial')
            migrate_to = ('django_enum_tests_edit_tests', '0001_initial')

            @classmethod
            def setUpClass(cls):
                set_models(1)
                super().setUpClass()

            def test_0001_initial(self):

                MigrationTester = self.new_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                # Let's create a model with just a single field specified:
                for int_enum, color in [
                    (0, 'R'),
                    (1, 'G'),
                    (2, 'B'),
                    (0, 'K'),
                ]:
                    MigrationTester.objects.create(int_enum=int_enum, color=color)

                self.assertEqual(len(MigrationTester._meta.get_fields()), 3)
                self.assertEqual(
                    MigrationTester.objects.filter(int_enum=0).count(), 2)
                self.assertEqual(
                    MigrationTester.objects.filter(int_enum=1).count(), 1)
                self.assertEqual(
                    MigrationTester.objects.filter(int_enum=2).count(), 1)

                self.assertEqual(MigrationTester.objects.filter(color='R').count(),
                                 1)
                self.assertEqual(MigrationTester.objects.filter(color='G').count(),
                                 1)
                self.assertEqual(MigrationTester.objects.filter(color='B').count(),
                                 1)
                self.assertEqual(MigrationTester.objects.filter(color='K').count(),
                                 1)

                # todo the constraints are failing these tests because they are
                #   changed before the data is changed - these tests need to be
                #   updated to change the data between the constraint changes

            def test_0001_code(self):
                from .edit_tests.models import MigrationTester

                # Let's create a model with just a single field specified:
                for int_enum, color in [
                    (MigrationTester.IntEnum(0), MigrationTester.Color((1, 0, 0))),
                    (MigrationTester.IntEnum['TWO'],
                     MigrationTester.Color('00FF00')),
                    (MigrationTester.IntEnum.THREE, MigrationTester.Color('Blue')),
                    (MigrationTester.IntEnum.ONE, MigrationTester.Color.BLACK),
                ]:
                    MigrationTester.objects.create(int_enum=int_enum, color=color)

                for obj in MigrationTester.objects.all():
                    self.assertIsInstance(
                        obj.int_enum,
                        MigrationTester.IntEnum
                    )
                    self.assertIsInstance(
                        obj.color,
                        MigrationTester.Color
                    )

                self.assertEqual(MigrationTester.objects.filter(
                    int_enum=MigrationTester.IntEnum.ONE).count(), 2)
                self.assertEqual(MigrationTester.objects.filter(
                    int_enum=MigrationTester.IntEnum(1)).count(), 1)
                self.assertEqual(MigrationTester.objects.filter(
                    int_enum=MigrationTester.IntEnum['THREE']).count(), 1)

                self.assertEqual(
                    MigrationTester.objects.filter(color=(1, 0, 0)).count(), 1)
                self.assertEqual(
                    MigrationTester.objects.filter(color='GREEN').count(), 1)
                self.assertEqual(
                    MigrationTester.objects.filter(color='Blue').count(), 1)
                self.assertEqual(
                    MigrationTester.objects.filter(color='000000').count(), 1)

                MigrationTester.objects.all().delete()


        class TestAlterValuesMigration(ResetModelsMixin, MigratorTestCase):

            migrate_from = ('django_enum_tests_edit_tests', '0001_initial')
            migrate_to = ('django_enum_tests_edit_tests', '0002_alter_values')

            @classmethod
            def setUpClass(cls):
                set_models(2)
                super().setUpClass()

            def prepare(self):

                MigrationTester = self.old_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                # Let's create a model with just a single field specified:
                for int_enum, color in [
                    (0, 'R'),
                    (1, 'G'),
                    (2, 'B'),
                    (0, 'K'),
                ]:
                    MigrationTester.objects.create(int_enum=int_enum, color=color)

            def test_0002_alter_values(self):

                MigrationTesterNew = self.new_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum=0).count(), 0)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum=1).count(), 2)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum=2).count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum=3).count(), 1)

                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='R').count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='G').count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='B').count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='K').count(), 1)

            def test_0002_code(self):
                from .edit_tests.models import MigrationTester

                MigrationTester.objects.all().delete()

                # Let's create a model with just a single field specified:
                for int_enum, color in [
                    (MigrationTester.IntEnum(1), MigrationTester.Color((1, 0, 0))),
                    (MigrationTester.IntEnum['TWO'],
                     MigrationTester.Color('00FF00')),
                    (MigrationTester.IntEnum.THREE, MigrationTester.Color('Blue')),
                    (MigrationTester.IntEnum.ONE, MigrationTester.Color.BLACK),
                ]:
                    MigrationTester.objects.create(int_enum=int_enum, color=color)

                for obj in MigrationTester.objects.all():
                    self.assertIsInstance(
                        obj.int_enum,
                        MigrationTester.IntEnum
                    )
                    self.assertIsInstance(
                        obj.color,
                        MigrationTester.Color
                    )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum.ONE,
                        color=(1, 0, 0)
                    ).count(), 1)

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum.ONE,
                        color=MigrationTester.Color.BLACK
                    ).count(), 1)

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum(2),
                        color='GREEN'
                    ).count(), 1)

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=3,
                        color='Blue'
                    ).count(), 1)

                MigrationTester.objects.all().delete()


        class TestRemoveBlackMigration(ResetModelsMixin, MigratorTestCase):

            migrate_from = ('django_enum_tests_edit_tests', '0002_alter_values')
            migrate_to = ('django_enum_tests_edit_tests', '0003_remove_black')

            @classmethod
            def setUpClass(cls):
                set_models(3)
                super().setUpClass()

            def prepare(self):

                MigrationTester = self.old_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                # Let's create a model with just a single field specified:
                for int_enum, color in [
                    (1, 'R'),
                    (2, 'G'),
                    (3, 'B'),
                    (1, 'K'),
                ]:
                    MigrationTester.objects.create(int_enum=int_enum, color=color)

            def test_0003_remove_black(self):

                MigrationTesterNew = self.new_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum=0).count(), 0)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum=1).count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum=2).count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum=3).count(), 1)

                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='R').count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='G').count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='B').count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='K').count(), 0)

            def test_0003_code(self):
                from .edit_tests.models import MigrationTester

                MigrationTester.objects.all().delete()

                self.assertFalse(hasattr(MigrationTester.Color, 'BLACK'))

                # Let's create a model with just a single field specified:
                for int_enum, color in [
                    (MigrationTester.IntEnum(1), MigrationTester.Color((1, 0, 0))),
                    (MigrationTester.IntEnum['TWO'],
                     MigrationTester.Color('00FF00')),
                    (MigrationTester.IntEnum.THREE, MigrationTester.Color('Blue'))
                ]:
                    MigrationTester.objects.create(int_enum=int_enum, color=color)

                for obj in MigrationTester.objects.all():
                    self.assertIsInstance(
                        obj.int_enum,
                        MigrationTester.IntEnum
                    )
                    self.assertIsInstance(
                        obj.color,
                        MigrationTester.Color
                    )

                self.assertEqual(MigrationTester.objects.count(), 3)

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum.ONE,
                        color=(1, 0, 0)
                    ).count(), 1)

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum(2),
                        color='GREEN'
                    ).count(), 1)

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=3,
                        color='Blue'
                    ).count(), 1)

                MigrationTester.objects.all().delete()


        class TestConstrainedButNonStrict(ResetModelsMixin, MigratorTestCase):

            migrate_from = ('django_enum_tests_edit_tests', '0002_alter_values')
            migrate_to = ('django_enum_tests_edit_tests', '0003_remove_black')

            @classmethod
            def setUpClass(cls):
                set_models(4)
                super().setUpClass()

            def test_constrained_non_strict(self):
                set_models(4)
                from django.db.utils import IntegrityError

                from .edit_tests.models import MigrationTester
                self.assertRaises(
                    IntegrityError,
                    MigrationTester.objects.create,
                    int_enum=42,
                    color='R'
                )


        class TestRemoveConstraintMigration(ResetModelsMixin, MigratorTestCase):

            migrate_from = ('django_enum_tests_edit_tests', '0003_remove_black')
            migrate_to = ('django_enum_tests_edit_tests', '0004_remove_constraint')

            @classmethod
            def setUpClass(cls):
                set_models(5)
                super().setUpClass()

            def test_remove_contraint_code(self):
                # no migration was generated for this model class change
                from .edit_tests.models import MigrationTester

                MigrationTester.objects.all().delete()

                for int_enum, color in [
                    (MigrationTester.IntEnum.ONE, MigrationTester.Color.RD),
                    (MigrationTester.IntEnum(2), MigrationTester.Color('GR')),
                    (MigrationTester.IntEnum['THREE'],
                     MigrationTester.Color('0000ff')),
                    (42, MigrationTester.Color('Blue'))
                ]:
                    MigrationTester.objects.create(int_enum=int_enum, color=color)

                for obj in MigrationTester.objects.all():
                    if obj.int_enum != 42:
                        self.assertIsInstance(
                            obj.int_enum,
                            MigrationTester.IntEnum
                        )
                    self.assertIsInstance(
                        obj.color,
                        MigrationTester.Color
                    )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum(1),
                        color=MigrationTester.Color('RD')
                    ).count(),
                    1
                )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum.TWO,
                        color=MigrationTester.Color((0, 1, 0))
                    ).count(),
                    1
                )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum['THREE'],
                        color=MigrationTester.Color('Blue')
                    ).count(),
                    1
                )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=42,
                        color=MigrationTester.Color('Blue')
                    ).count(),
                    1
                )
                self.assertEqual(MigrationTester.objects.get(int_enum=42).int_enum,
                                 42)

                self.assertEqual(
                    MigrationTester.objects.count(),
                    4
                )

                MigrationTester.objects.all().delete()


        class TestRemoveIntEnumMigration(ResetModelsMixin, MigratorTestCase):

            migrate_from = ('django_enum_tests_edit_tests', '0003_remove_black')
            migrate_to = ('django_enum_tests_edit_tests', '0005_remove_int_enum')

            @classmethod
            def setUpClass(cls):
                set_models(6)
                super().setUpClass()

            def prepare(self):

                MigrationTester = self.old_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                # Let's create a model with just a single field specified:
                for int_enum, color in [
                    (1, 'R'),
                    (2, 'G'),
                    (3, 'B'),
                ]:
                    MigrationTester.objects.create(int_enum=int_enum, color=color)

            def test_0005_remove_int_enum(self):
                from django.core.exceptions import (
                    FieldDoesNotExist,
                    FieldError,
                )

                MigrationTesterNew = self.new_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                self.assertRaises(
                    FieldDoesNotExist,
                    MigrationTesterNew._meta.get_field,
                    'int_num'
                )
                self.assertRaises(
                    FieldError,
                    MigrationTesterNew.objects.filter,
                    {'int_enum': 1}
                )

            def test_0005_code(self):
                from .edit_tests.models import MigrationTester

                MigrationTester.objects.all().delete()

                for color in [
                    MigrationTester.Color.RD,
                    MigrationTester.Color('GR'),
                    MigrationTester.Color('0000ff')
                ]:
                    MigrationTester.objects.create(color=color)

                for obj in MigrationTester.objects.all():
                    self.assertFalse(hasattr(obj, 'int_enum'))
                    self.assertIsInstance(
                        obj.color,
                        MigrationTester.Color
                    )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        color=MigrationTester.Color('RD')
                    ).count(),
                    1
                )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        color=MigrationTester.Color((0, 1, 0))
                    ).count(),
                    1
                )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        color=MigrationTester.Color('Blue')
                    ).count(),
                    1
                )

                self.assertEqual(
                    MigrationTester.objects.count(),
                    3
                )

                MigrationTester.objects.all().delete()


        class TestAddIntEnumMigration(ResetModelsMixin, MigratorTestCase):

            migrate_from = ('django_enum_tests_edit_tests', '0005_remove_int_enum')
            migrate_to = ('django_enum_tests_edit_tests', '0006_add_int_enum')

            @classmethod
            def setUpClass(cls):
                set_models(7)
                super().setUpClass()

            def prepare(self):

                MigrationTester = self.old_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                # Let's create a model with just a single field specified:
                for color in ['R', 'G', 'B']:
                    MigrationTester.objects.create(color=color)

            def test_0006_add_int_enum(self):
                from django.core.exceptions import (
                    FieldDoesNotExist,
                    FieldError,
                )

                MigrationTesterNew = self.new_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                self.assertEqual(
                    MigrationTesterNew.objects.filter(
                        int_enum__isnull=True).count(),
                    3
                )

                MigrationTesterNew.objects.filter(color='R').update(int_enum='A')
                MigrationTesterNew.objects.filter(color='G').update(int_enum='B')
                MigrationTesterNew.objects.filter(color='B').update(int_enum='C')

                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum='0').count(), 0)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum='1').count(), 0)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum='2').count(), 0)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum='3').count(), 0)

                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum='A').count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum='B').count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(int_enum='C').count(), 1)

                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='R').count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='G').count(), 1)
                self.assertEqual(
                    MigrationTesterNew.objects.filter(color='B').count(), 1)

            def test_0006_code(self):
                from .edit_tests.models import MigrationTester

                MigrationTester.objects.all().delete()

                for int_enum, color in [
                    (MigrationTester.IntEnum.A, MigrationTester.Color.RED),
                    (MigrationTester.IntEnum('B'), MigrationTester.Color('Green')),
                    (
                    MigrationTester.IntEnum['C'], MigrationTester.Color('0000ff')),
                ]:
                    MigrationTester.objects.create(int_enum=int_enum, color=color)

                for obj in MigrationTester.objects.all():
                    self.assertIsInstance(
                        obj.int_enum,
                        MigrationTester.IntEnum
                    )
                    self.assertIsInstance(
                        obj.color,
                        MigrationTester.Color
                    )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum('A'),
                        color=MigrationTester.Color('Red')
                    ).count(),
                    1
                )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum.B,
                        color=MigrationTester.Color((0, 1, 0))
                    ).count(),
                    1
                )

                self.assertEqual(
                    MigrationTester.objects.filter(
                        int_enum=MigrationTester.IntEnum['C'],
                        color=MigrationTester.Color('BLUE')
                    ).count(),
                    1
                )

                self.assertEqual(
                    MigrationTester.objects.count(),
                    3
                )

                self.assertRaises(
                    ValueError,
                    MigrationTester.objects.create,
                    int_enum='D',
                    color=MigrationTester.Color('Blue')
                )

                MigrationTester.objects.all().delete()


        class TestChangeDefaultIndirectlyMigration(
            ResetModelsMixin,
            MigratorTestCase
        ):

            migrate_from = ('django_enum_tests_edit_tests', '0007_set_default')
            migrate_to = ('django_enum_tests_edit_tests', '0008_change_default')

            @classmethod
            def setUpClass(cls):
                set_models(8)
                super().setUpClass()

            def prepare(self):

                MigrationTester = self.old_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                MigrationTester.objects.create()

            def test_0008_change_default(self):
                from django.core.exceptions import (
                    FieldDoesNotExist,
                    FieldError,
                )

                MigrationTesterNew = self.new_state.apps.get_model(
                    'django_enum_tests_edit_tests',
                    'MigrationTester'
                )

                self.assertEqual(
                    MigrationTesterNew.objects.first().color,
                    'K'
                )

                self.assertEqual(
                    MigrationTesterNew.objects.create().color,
                    'B'
                )


        def test_migration_test_marker_tag():
            """Ensure ``MigratorTestCase`` sublasses are properly tagged."""
            assert MIGRATION_TEST_MARKER in TestInitialMigration.tags
            assert MIGRATION_TEST_MARKER in TestAlterValuesMigration.tags
            assert MIGRATION_TEST_MARKER in TestRemoveBlackMigration.tags
            assert MIGRATION_TEST_MARKER in TestRemoveIntEnumMigration.tags
            assert MIGRATION_TEST_MARKER in TestAddIntEnumMigration.tags


    class TestChoicesEnumProp(TestChoices):

        MODEL_CLASS = EnumTester

        @property
        def create_params(self):
            return {
                'small_pos_int': self.SmallPosIntEnum.VAL2,
                'small_int': 'Value -32768',
                'pos_int': 2147483647,
                'int': -2147483648,
                'big_pos_int': 'Value 2147483648',
                'big_int': 'VAL2',
                'constant': 'φ',
                'text': 'V TWo',
                'extern': 'two',
                'date_enum': date(year=1984, month=8, day=7),
                'datetime_enum': datetime(1991, 6, 15, 20, 9, 0),
                'duration_enum': timedelta(weeks=2),
                'time_enum': time(hour=9),
                'decimal_enum': Decimal('99.9999'),
                'constant': self.Constants.GOLDEN_RATIO,
            }

        @property
        def values_params(self):
            return {
                'small_pos_int': self.SmallPosIntEnum.VAL2,
                'small_int': 'Value -32768',
                'pos_int': 2147483647,
                'int': -2147483648,
                'big_pos_int': 'Value 2147483648',
                'big_int': 'VAL2',
                'constant': 'φ',
                'text': 'V TWo',
                'extern': 'two',
                'dj_int_enum': 3,
                'dj_text_enum': self.DJTextEnum.A,
                'non_strict_int': 75,
                'non_strict_text':  'arbitrary',
                'no_coerce': self.SmallPosIntEnum.VAL2
            }

        def test_values(self):
            from django.db.models.fields import NOT_PROVIDED
            values1, values2 = super().do_test_values()

            # also test equality symmetry
            self.assertEqual(values1['small_pos_int'], 'Value 2')
            self.assertEqual(values1['small_int'], 'Value -32768')
            self.assertEqual(values1['pos_int'], 2147483647)
            self.assertEqual(values1['int'], -2147483648)
            self.assertEqual(values1['big_pos_int'], 'Value 2147483648')
            self.assertEqual(values1['big_int'], 'VAL2')
            self.assertEqual(values1['constant'], 'φ')
            self.assertEqual(values1['text'], 'V TWo')
            self.assertEqual(values1['extern'], 'Two')

            for field in [
                'small_pos_int',
                'small_int',
                'pos_int',
                'int',
                'big_pos_int',
                'big_int',
                'constant',
                'text'
            ]:
                default = self.MODEL_CLASS._meta.get_field(field).default
                if default is NOT_PROVIDED:
                    default = None
                self.assertEqual(values2[field], default)

        def test_validate(self):
            tester = super().do_test_validate()

            self.assertTrue(tester._meta.get_field('small_int').validate('Value -32768', tester) is None)
            self.assertTrue(tester._meta.get_field('pos_int').validate(2147483647, tester) is None)
            self.assertTrue(tester._meta.get_field('int').validate('VALn1', tester) is None)
            self.assertTrue(tester._meta.get_field('big_pos_int').validate('Value 2147483648', tester) is None)
            self.assertTrue(tester._meta.get_field('big_int').validate(self.BigPosIntEnum.VAL2, tester) is None)
            self.assertTrue(tester._meta.get_field('constant').validate('φ', tester) is None)
            self.assertTrue(tester._meta.get_field('text').validate('default', tester) is None)

            self.assertTrue(tester._meta.get_field('dj_int_enum').validate(1, tester) is None)
            self.assertTrue(tester._meta.get_field('dj_text_enum').validate('A', tester) is None)
            self.assertTrue(tester._meta.get_field('non_strict_int').validate(20, tester) is None)


    class FlagTestsProp(FlagTests):

        MODEL_CLASS = EnumFlagPropTester

        def test_prop_enum(self):

            from django_enum.tests.enum_prop.enums import (
                GNSSConstellation,
                SmallNegativeFlagEnum,
                SmallPositiveFlagEnum,
            )

            self.assertEqual(GNSSConstellation.GPS, GNSSConstellation('gps'))
            self.assertEqual(GNSSConstellation.GLONASS, GNSSConstellation('GLONASS'))
            self.assertEqual(GNSSConstellation.GALILEO, GNSSConstellation('galileo'))
            self.assertEqual(GNSSConstellation.BEIDOU, GNSSConstellation('BeiDou'))
            self.assertEqual(GNSSConstellation.QZSS, GNSSConstellation('qzss'))

            self.assertEqual(choices(SmallNegativeFlagEnum), SmallNegativeFlagEnum.choices)
            self.assertEqual(names(SmallNegativeFlagEnum), SmallNegativeFlagEnum.names)

            self.assertEqual(choices(SmallPositiveFlagEnum), SmallPositiveFlagEnum.choices)
            self.assertEqual(names(SmallPositiveFlagEnum), SmallPositiveFlagEnum.names)


    class ExampleTests(TestCase):  # pragma: no cover  - why is this necessary?

        def test_mapboxstyle(self):
            from django_enum.tests.examples.models import Map

            map_obj = Map.objects.create()

            self.assertTrue(
                map_obj.style.uri == 'mapbox://styles/mapbox/streets-v11'
            )

            # uri's are symmetric
            map_obj.style = 'mapbox://styles/mapbox/light-v10'
            self.assertTrue(map_obj.style == Map.MapBoxStyle.LIGHT)
            self.assertTrue(map_obj.style == 3)
            self.assertTrue(map_obj.style == 'light')

            # so are labels (also case insensitive)
            map_obj.style = 'satellite streets'
            self.assertTrue(map_obj.style == Map.MapBoxStyle.SATELLITE_STREETS)

            # when used in API calls (coerced to strings) - they "do the right
            # thing"
            self.assertTrue(
                str(map_obj.style) ==
                'mapbox://styles/mapbox/satellite-streets-v11'
            )

        def test_color(self):
            from django_enum.tests.examples.models import TextChoicesExample

            instance = TextChoicesExample.objects.create(
                color=TextChoicesExample.Color('FF0000')
            )
            self.assertTrue(
                instance.color == TextChoicesExample.Color('Red') ==
                TextChoicesExample.Color('R') == TextChoicesExample.Color((1, 0, 0))
            )

            # direct comparison to any symmetric value also works
            self.assertTrue(instance.color == 'Red')
            self.assertTrue(instance.color == 'R')
            self.assertTrue(instance.color == (1, 0, 0))

            # save by any symmetric value
            instance.color = 'FF0000'

            # access any property right from the model field
            self.assertTrue(instance.color.hex == 'ff0000')

            # this also works!
            self.assertTrue(instance.color == 'ff0000')

            # and so does this!
            self.assertTrue(instance.color == 'FF0000')

            instance.save()

            self.assertTrue(
                TextChoicesExample.objects.filter(
                    color=TextChoicesExample.Color.RED
                ).first() == instance
            )

            self.assertTrue(
                TextChoicesExample.objects.filter(
                    color=(1, 0, 0)
                ).first() == instance
            )

            self.assertTrue(
                TextChoicesExample.objects.filter(
                    color='FF0000'
                ).first() == instance
            )

            from django.forms import ModelForm
            from django_enum import EnumChoiceField

            class TextChoicesExampleForm(ModelForm):
                color = EnumChoiceField(TextChoicesExample.Color)

                class Meta:
                    model = TextChoicesExample
                    fields = '__all__'

            # this is possible
            form = TextChoicesExampleForm({'color': 'FF0000'})
            form.save()
            self.assertTrue(form.instance.color == TextChoicesExample.Color.RED)

        def test_strict(self):
            from django_enum.tests.examples.models import StrictExample
            obj = StrictExample()

            # set to a valid EnumType value
            obj.non_strict = '1'
            # when accessed will be an EnumType instance
            self.assertTrue(obj.non_strict is StrictExample.EnumType.ONE)

            # we can also store any string less than or equal to length 10
            obj.non_strict = 'arbitrary'
            obj.full_clean()  # no errors
            # when accessed will be a str instance
            self.assertTrue(obj.non_strict == 'arbitrary')

        def test_basic(self):
            from django_enum.tests.examples.models import MyModel
            instance = MyModel.objects.create(
                txt_enum=MyModel.TextEnum.VALUE1,
                int_enum=3  # by-value assignment also works
            )

            self.assertTrue(instance.txt_enum == MyModel.TextEnum('V1'))
            self.assertTrue(instance.txt_enum.label == 'Value 1')

            self.assertTrue(instance.int_enum == MyModel.IntEnum['THREE'])
            self.assertTrue(instance.int_enum.value == 3)

            self.assertRaises(
                ValueError,
                MyModel.objects.create,
                txt_enum='AA',
                int_enum=3
            )

            instance.txt_enum = 'AA'
            self.assertRaises(ValidationError, instance.full_clean)

        def test_no_coerce(self):
            from django_enum.tests.examples.models import NoCoerceExample

            obj = NoCoerceExample()
            # set to a valid EnumType value
            obj.non_strict = '1'
            obj.full_clean()

            # when accessed from the db or after clean, will be the primitive value
            self.assertTrue(obj.non_strict == '1')
            self.assertTrue(isinstance(obj.non_strict, str))
            self.assertFalse(isinstance(obj.non_strict, NoCoerceExample.EnumType))

else:  # pragma: no cover
    pass


class TestEnumConverter(TestCase):

    def test_enum_converter(self):
        from django.urls import reverse
        from django.urls.converters import get_converter
        from django_enum.tests.converters.urls import Enum1, record
        from django_enum.tests.djenum.enums import Constants, DecimalEnum

        converter = get_converter('Enum1')
        self.assertEqual(converter.regex, '1|2')
        self.assertEqual(converter.to_python('1'), Enum1.A)
        self.assertEqual(converter.to_python('2'), Enum1.B)
        self.assertEqual(converter.primitive, int)
        self.assertEqual(converter.enum, Enum1)
        self.assertEqual(converter.prop, 'value')

        self.assertEqual(
            reverse('enum1_view', kwargs={'enum': Enum1.A}),
            '/1'
        )

        response = self.client.get('/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(record[0], Enum1.A)

        converter = get_converter('decimal_enum')
        self.assertEqual(converter.regex, '0.99|0.999|0.9999|99.9999|999')
        self.assertEqual(converter.to_python('0.999'), DecimalEnum.TWO)
        self.assertEqual(converter.to_python('99.9999'), DecimalEnum.FOUR)
        self.assertEqual(converter.primitive, Decimal)
        self.assertEqual(converter.enum, DecimalEnum)
        self.assertEqual(converter.prop, 'value')

        self.assertEqual(
            reverse('decimal_enum_view', kwargs={'enum': DecimalEnum.ONE}),
            '/0.99'
        )

        response = self.client.get('/0.99')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(record[1], DecimalEnum.ONE)

        converter = get_converter('Constants')
        self.assertEqual(converter.regex, "Pi|Euler's Number|Golden Ratio")
        self.assertEqual(converter.to_python('Golden Ratio'), Constants.GOLDEN_RATIO)
        self.assertEqual(converter.to_python("Euler's Number"), Constants.e)
        self.assertEqual(converter.to_python('Pi'), Constants.PI)
        self.assertEqual(converter.primitive, float)
        self.assertEqual(converter.enum, Constants)
        self.assertEqual(converter.prop, 'label')

        self.assertEqual(
            reverse('constants_view', kwargs={'enum': Constants.GOLDEN_RATIO}),
            '/Golden%20Ratio'
        )

        response = self.client.get("/Euler's Number")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(record[2], Constants.e)


class ConstraintTests(EnumTypeMixin, TestCase):
    """Test that Django's choices types work as expected"""

    MODEL_CLASS = EnumTester

    def test_constraint_naming(self):
        from django_enum.fields import MAX_CONSTRAINT_NAME_LENGTH

        name = f'{self.MODEL_CLASS._meta.app_label}_EnumTester_small_pos_int_SmallPosIntEnum'

        self.assertEqual(
            EnumField.constraint_name(
                self.MODEL_CLASS,
                'small_pos_int',
                self.SmallPosIntEnum
            ),
            name[len(name)-MAX_CONSTRAINT_NAME_LENGTH:]
        )

        self.assertEqual(
            EnumField.constraint_name(
                self.MODEL_CLASS,
                'small_int',
                self.SmallIntEnum
            ),
            f'{self.MODEL_CLASS._meta.app_label}_EnumTester_small_int_SmallIntEnum'
        )

    # def test_primitive_constraints(self):
    #     from django.db import connection
    #     from django_enum.tests.djenum.models import MultiPrimitiveTestModel
    #
    #     table_name = MultiPrimitiveTestModel._meta.db_table
    #     multi = MultiPrimitiveTestModel._meta.get_field('multi')
    #     multi_float = MultiPrimitiveTestModel._meta.get_field('multi_float')
    #     multi_none = MultiPrimitiveTestModel._meta.get_field('multi_none')
    #     multi_none_unconstrained = MultiPrimitiveTestModel._meta.get_field('multi_none_unconstrained')
    #
    #
    #     with connection.cursor() as cursor:
    #         # Try to insert a person with negative age
    #         cursor.execute(
    #             f"INSERT INTO {table_name} ({multi.column}) VALUES (-5)"
    #         )
    #
    #         # Fetch the results
    #         cursor.execute(
    #             f"SELECT {column_name} FROM {table_name} WHERE {column_name} < 0")
    #         rows = cursor.fetchall()
    #
    #         # Assert that no rows are returned (i.e., the check constraint worked)
    #         self.assertEqual(len(rows), 0)
