import os
from pathlib import Path
from time import perf_counter

from bs4 import BeautifulSoup as Soup
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import transaction
from django.http import QueryDict
from django.test import Client, TestCase
from django.urls import reverse
from django_enum import TextChoices
from django_enum.tests.djenum.enums import (
    BigIntEnum,
    BigPosIntEnum,
    Constants,
    DJIntEnum,
    DJTextEnum,
    IntEnum,
    PosIntEnum,
    SmallIntEnum,
    SmallPosIntEnum,
    TextEnum,
)
from django_enum.forms import EnumChoiceField
from django_enum.tests.djenum.forms import EnumTesterForm
from django_enum.tests.djenum.models import EnumTester
from django_test_migrations.constants import MIGRATION_TEST_MARKER
from django_test_migrations.contrib.unittest_case import MigratorTestCase

try:
    import django_filters
    DJANGO_FILTERS_INSTALLED = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    DJANGO_FILTERS_INSTALLED = False

try:
    import enum_properties
    ENUM_PROPERTIES_INSTALLED = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    ENUM_PROPERTIES_INSTALLED = False


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
    def DJIntEnum(self):
        return self.MODEL_CLASS._meta.get_field('dj_int_enum').enum

    @property
    def DJTextEnum(self):
        return self.MODEL_CLASS._meta.get_field('dj_text_enum').enum

    def enum_type(self, field_name):
        return self.MODEL_CLASS._meta.get_field(field_name).enum

    def enum_primitive(self, field_name):
        enum_type = self.enum_type(field_name)
        if enum_type in {
            self.SmallPosIntEnum, self.SmallIntEnum, self.IntEnum,
            self.PosIntEnum, self.BigIntEnum, self.BigPosIntEnum,
            self.DJIntEnum
        }:
            return int
        elif enum_type is self.Constants:
            return float
        elif enum_type in {self.TextEnum, self.DJTextEnum}:
            return str
        else:  # pragma: no cover
            raise RuntimeError(f'Missing enum type primitive for {enum_type}')


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
            'text': self.TextEnum.VALUE2
        }

    def test_basic_save(self):
        self.MODEL_CLASS.objects.all().delete()
        self.MODEL_CLASS.objects.create(**self.create_params)
        for param, value in self.create_params.items():
            self.assertEqual(self.MODEL_CLASS.objects.filter(**{param: value}).count(), 1)
        self.MODEL_CLASS.objects.all().delete()

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
            'small_pos_int': SmallPosIntEnum.VAL2,
            'small_int': SmallIntEnum.VALn1,
            'pos_int': PosIntEnum.VAL3,
            'int': IntEnum.VALn1,
            'big_pos_int': BigPosIntEnum.VAL3,
            'big_int': BigIntEnum.VAL2,
            'constant': Constants.GOLDEN_RATIO,
            'text': TextEnum.VALUE2,
            'dj_int_enum': 3,
            'dj_text_enum': DJTextEnum.A,
            'non_strict_int':  75
        }

    def test_values(self):
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
        self.assertEqual(values1['dj_int_enum'], self.DJIntEnum.THREE)
        self.assertEqual(values1['dj_text_enum'], self.DJTextEnum.A)
        self.assertEqual(values1['non_strict_int'], 75)

        obj.delete()

        obj = self.MODEL_CLASS.objects.create(
            non_strict_int=self.SmallPosIntEnum.VAL1
        )
        values2 = self.MODEL_CLASS.objects.filter(pk=obj.pk).values().first()
        self.assertEqual(values2['non_strict_int'], self.SmallPosIntEnum.VAL1)

        self.assertEqual(values2['dj_int_enum'], 1)
        self.assertEqual(values2['dj_text_enum'], 'A')

        return values1, values2

    def test_non_strict(self):
        """
        Test that non strict fields allow assignment and read of non-enum values.
        """
        values = {
            self.SmallPosIntEnum.VAL1,
            self.SmallPosIntEnum.VAL2,
            self.SmallPosIntEnum.VAL3,
            10,
            12,
            15
        }
        for value in values:
            self.MODEL_CLASS.objects.create(non_strict_int=value)

        for obj in self.MODEL_CLASS.objects.filter(non_strict_int__isnull=False):
            self.assertTrue(obj.non_strict_int in values)

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(non_strict_int=self.SmallPosIntEnum.VAL1).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(non_strict_int=self.SmallPosIntEnum.VAL2).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(non_strict_int=self.SmallPosIntEnum.VAL3).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(non_strict_int=10).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(non_strict_int=12).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(non_strict_int=15).count(), 1
        )

    def test_serialization(self):
        tester = self.MODEL_CLASS.objects.create(**self.values_params)

        serialized = serializers.serialize('json', self.MODEL_CLASS.objects.all())

        tester.delete()

        for mdl in serializers.deserialize('json', serialized):
            mdl.save()
            tester = mdl.object

        for param, value in self.values_params.items():
            self.assertEqual(getattr(tester, param), value)

    def test_validate(self):
        tester = self.MODEL_CLASS.objects.create()
        self.assertRaises(ValidationError, tester._meta.get_field('small_pos_int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('small_int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('pos_int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('big_pos_int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('big_int').validate, 666, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('constant').validate, 66.6, tester)
        self.assertRaises(ValidationError, tester._meta.get_field('text').validate, '666', tester)

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

        return tester

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

    def test_base_fields(self):
        """
        Test that the Enum metaclass picks the correct database field type for each enum.
        """
        tester = self.MODEL_CLASS.objects.create()
        from django.db.models import (
            BigIntegerField,
            CharField,
            FloatField,
            IntegerField,
            PositiveBigIntegerField,
            PositiveIntegerField,
            PositiveSmallIntegerField,
            SmallIntegerField,
        )

        self.assertIsInstance(tester._meta.get_field('small_int'), SmallIntegerField)
        self.assertEqual(tester.small_int, tester._meta.get_field('small_int').default)
        self.assertEqual(tester.small_int, SmallIntEnum.VAL3)
        self.assertIsInstance(tester._meta.get_field('small_pos_int'), PositiveSmallIntegerField)
        self.assertIsNone(tester.small_pos_int)
        self.assertIsInstance(tester._meta.get_field('int'), IntegerField)
        self.assertIsNone(tester.int)

        self.assertIsInstance(tester._meta.get_field('pos_int'), PositiveIntegerField)
        self.assertEqual(tester.pos_int, tester._meta.get_field('pos_int').default)
        self.assertEqual(tester.pos_int, PosIntEnum.VAL3)

        self.assertIsInstance(tester._meta.get_field('big_int'), BigIntegerField)
        self.assertEqual(tester.big_int, tester._meta.get_field('big_int').default)
        self.assertEqual(tester.big_int, BigIntEnum.VAL0)

        self.assertIsInstance(tester._meta.get_field('big_pos_int'), PositiveBigIntegerField)
        self.assertIsNone(tester.big_pos_int)

        self.assertIsInstance(tester._meta.get_field('constant'), FloatField)
        self.assertIsNone(tester.constant)

        self.assertIsInstance(tester._meta.get_field('text'), CharField)
        self.assertEqual(tester._meta.get_field('text').max_length, 4)
        self.assertIsNone(tester.text)


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
            text=self.TextEnum.VALUE2
        )
        self.MODEL_CLASS.objects.create(
            small_pos_int=self.SmallPosIntEnum.VAL2,
            small_int=self.SmallIntEnum.VAL0,
            pos_int=self.PosIntEnum.VAL1,
            int=self.IntEnum.VALn1,
            big_pos_int=self.BigPosIntEnum.VAL3,
            big_int=self.BigIntEnum.VAL2,
            constant=self.Constants.GOLDEN_RATIO,
            text=self.TextEnum.VALUE2
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

        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, int_field='a')
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, float_field='a')
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, constant='PI')
        self.assertRaises(ValueError, self.MODEL_CLASS.objects.filter, big_pos_int='VAL3')
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
            'dj_int_enum': 2,
            'dj_text_enum': self.DJTextEnum.B,
            'non_strict_int': self.SmallPosIntEnum.VAL2
        }

    @property
    def bad_values(self):
        return {
            'small_pos_int': 4.1,
            'small_int': 'Value 2',
            'pos_int': 5.3,
            'int': 10,
            'big_pos_int': '-12',
            'big_int': '-12',
            'constant': 2.7,
            'text': '143 emma',
            'dj_int_enum': '',
            'dj_text_enum': 'D',
            'non_strict_int': 'Not an int'
        }

    def test_initial(self):
        form = self.FORM_CLASS(initial=self.model_params)
        for field, value in self.model_params.items():
            self.assertIsInstance(form[field].value(), self.enum_primitive(field))
            self.assertEqual(form[field].value(), self.enum_type(field)(value).value)
            self.assertIsInstance(
                form[field].field.to_python(form[field].value()),
                self.enum_type(field))

    def test_instance(self):
        instance = self.MODEL_CLASS.objects.create(**self.model_params)
        form = self.FORM_CLASS(instance=instance)
        for field, value in self.model_params.items():
            self.assertIsInstance(form[field].value(), self.enum_primitive(field))
            self.assertEqual(form[field].value(), self.enum_type(field)(value).value)
            self.assertIsInstance(
                form[field].field.to_python(form[field].value()),
                self.enum_type(field))
        instance.delete()

    def test_data(self):
        form = self.FORM_CLASS(data=self.model_params)
        form.full_clean()
        self.assertTrue(form.is_valid())
        for field, value in self.model_params.items():
            self.assertIsInstance(form[field].value(), self.enum_primitive(field))
            self.assertEqual(form[field].value(), self.enum_type(field)(value).value)
            self.assertIsInstance(form[field].field.to_python(form[field].value()), self.enum_type(field))

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
            (EnumChoiceField(SmallIntEnum), 123123123),
            (EnumChoiceField(PosIntEnum), -1),
            (EnumChoiceField(IntEnum), '63'),
            (EnumChoiceField(BigPosIntEnum), None),
            (EnumChoiceField(BigIntEnum), ''),
            (EnumChoiceField(Constants), 'y'),
            (EnumChoiceField(TextEnum), 42),
            (EnumChoiceField(DJIntEnum), '5.3'),
            (EnumChoiceField(DJTextEnum), 12),
            (EnumChoiceField(SmallPosIntEnum, strict=False), 'not an int')
        ]:
            self.assertRaises(ValidationError, enum_field.validate, bad_value)

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

    def setUp(self):
        self.values = {val: {} for val in self.compared_attributes}
        self.objects = []
        self.MODEL_CLASS.objects.all().delete()
        self.objects.append(
            self.MODEL_CLASS.objects.create()
        )
        self.objects.append(
            self.MODEL_CLASS.objects.create(
                small_pos_int=self.SmallPosIntEnum.VAL1,
                small_int=self.SmallIntEnum.VAL1,
                pos_int=self.PosIntEnum.VAL1,
                int=self.IntEnum.VAL1,
                big_pos_int=self.BigPosIntEnum.VAL1,
                big_int=self.BigIntEnum.VAL1,
                constant=self.Constants.PI,
                text=self.TextEnum.VALUE1
            )
        )
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
                    text=self.TextEnum.VALUE2
                )
            )
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
                    text=self.TextEnum.VALUE3
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
            'dj_int_enum': self.DJIntEnum.TWO,
            'dj_text_enum': self.DJTextEnum.C,
            'non_strict_int': self.SmallPosIntEnum.VAL1
        }

    @property
    def post_params_symmetric(self):
        return {
            **self.post_params,
        }

    def test_add(self):
        """
        Test that add forms work and that EnumField type allows creations
        from symmetric values
        """
        c = Client()

        # test normal choice field and our EnumChoiceField
        for form_url, params in [
            ('enum-add', self.post_params),
            ('enum-form-add', self.post_params_symmetric)
        ]:
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
                form_val = self.enum_primitive(param)(form_val)
                if param != 'non_strict_int':
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
        for form_url, params in [
            ('enum-update', self.post_params),
            ('enum-form-update', self.post_params_symmetric)
        ]:
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
                self.assertEqual(getattr(updated, param), value)
            updated.delete()

    def test_delete(self):
        c = Client()
        for form_url in ['enum-delete', 'enum-form-delete']:
            deleted = self.MODEL_CLASS.objects.create()
            c.delete(reverse(f'{self.NAMESPACE}:{form_url}', kwargs={'pk': deleted.pk}))
            self.assertRaises(self.MODEL_CLASS.DoesNotExist, self.MODEL_CLASS.objects.get, pk=deleted.pk)

    @staticmethod
    def get_enum_val(enum, value):
        if value is None or value == '':
            return None
        if int in enum.__mro__:
            return enum(int(value))
        if float in enum.__mro__:
            return enum(float(value))
        return enum(value)

    def test_add_form(self):
        c = Client()
        # test normal choice field and our EnumChoiceField
        for form_url in ['enum-add', 'enum-form-add']:
            response = c.get(reverse(f'{self.NAMESPACE}:{form_url}'))
            soup = Soup(response.content, features='html.parser')

            for field in [
                'small_pos_int',
                'small_int',
                'pos_int',
                'int',
                'big_pos_int',
                'big_int',
                'constant',
                'text',
                'dj_int_enum',
                'dj_text_enum',
                'non_strict_int'
            ]:
                field = EnumTester._meta.get_field(field)
                expected = dict(zip([en for en in field.enum], field.enum.labels))  # value -> label
                null_opt = False
                for option in soup.find('select', id=f'id_{field.name}').find_all('option'):
                    if (option['value'] is None or option['value'] == '') and option.text.count('-') >= 2:
                        self.assertTrue(field.blank or field.null)
                        null_opt = True
                        continue

                    try:
                        value = self.get_enum_val(field.enum, option['value'])
                        self.assertEqual(str(expected[value]), option.text)
                        del expected[value]
                    except KeyError:  # pragma: no cover
                        self.fail(f'{field.name} did not expect option {option["value"]}: {option.text}.')

                self.assertEqual(len(expected), 0)

                if not field.null and not field.blank:
                    self.assertFalse(null_opt, "An unexpected null option is present")  # pragma: no cover

    def verify_form(self, obj, soup):
        for field in [
            'small_pos_int',
            'small_int',
            'pos_int',
            'int',
            'big_pos_int',
            'big_int',
            'constant',
            'text',
        ]:
            field = EnumTester._meta.get_field(field)
            expected = dict(zip([en for en in field.enum],
                                field.enum.labels))  # value -> label
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
                        self.assertIsNone(getattr(obj, field.name))
                    else:  # pragma: no cover
                        pass
                    # (coverage error?? the line below gets hit)
                    continue  # pragma: no cover

                try:
                    value = self.get_enum_val(field.enum, option['value'])
                    self.assertEqual(str(expected[value]), option.text)
                    if option.has_attr('selected'):
                        self.assertEqual(getattr(obj, field.name), value)
                    del expected[value]
                except KeyError:  # pragma: no cover
                    self.fail(
                        f'{field.name} did not expect option {option["value"]}: {option.text}.')

            self.assertEqual(len(expected), 0)

            if not field.null and not field.blank:
                self.assertFalse(
                    null_opt,
                    "An unexpected null option is present"
                )  # pragma: no cover

    def test_update_form(self):
        client = Client()
        # test normal choice field and our EnumChoiceField
        for form_url in ['enum-update', 'enum-form-update']:
            for obj in self.objects:
                response = client.get(reverse(f'{self.NAMESPACE}:{form_url}', kwargs={'pk': obj.pk}))
                soup = Soup(response.content, features='html.parser')
                self.verify_form(obj, soup)

    def test_non_strict_select(self):
        client = Client()
        obj = self.MODEL_CLASS.objects.create(
            non_strict_int=233
        )
        for form_url in ['enum-update', 'enum-form-update']:
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
            'dj_int_enum': ['value'],
            'dj_text_enum': ['value'],
            'non_strict_int': ['value']
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
            'dj_int_enum',
            'dj_text_enum',
            'non_strict_int'
        ]

    def list_to_objects(self, resp_content):
        objects = {}
        for obj_div in resp_content.find('body').find_all(f'div', class_='enum'):
            objects[int(obj_div['data-obj-id'])] = {
                attr: self.get_enum_val(
                    self.MODEL_CLASS._meta.get_field(attr).enum,
                    obj_div.find(f'p', {'class': attr}).find(
                        'span', class_='value'
                    ).text
                )
                for attr in self.compared_attributes
            }
        return objects

    if DJANGO_FILTERS_INSTALLED:
        def test_django_filter(self):
            self.do_test_django_filter(
                reverse(f'{self.NAMESPACE}:enum-filter')
            )

        def do_test_django_filter(self, url):
            """
            Exhaustively test query parameter permutations based on data
            created in setUp
            """
            client = Client()
            for attr, val_map in self.values.items():
                for val, objs in val_map.items():
                    if val is None:
                        continue  # todo how to query None?
                    for prop in self.field_filter_properties[attr]:
                        qry = QueryDict(mutable=True)
                        prop_vals = getattr(val, prop)
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
            'dj_int_enum': 3,
            'dj_text_enum': self.DJTextEnum.A,
            'non_strict_int': 15
        }

    @property
    def update_params(self):
        return {
            'non_strict_int': 100,
            'constant': self.Constants.PI,
            'big_int': -2147483649
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


if ENUM_PROPERTIES_INSTALLED:

    from django_enum.forms import EnumChoiceField
    from django_enum.tests.enum_prop.enums import (
        BigIntEnum,
        BigPosIntEnum,
        Constants,
        DJIntEnum,
        DJTextEnum,
        IntEnum,
        PosIntEnum,
        PrecedenceTest,
        SmallIntEnum,
        SmallPosIntEnum,
        TextEnum,
    )
    from django_enum.tests.enum_prop.forms import EnumTesterForm
    from django_enum.tests.enum_prop.models import (
        EnumTester,
        MyModel,
        PerfCompare,
        SingleEnumPerf,
        SingleFieldPerf,
    )
    from enum_properties import EnumProperties, s


    class TestEnumPropertiesIntegration(TestCase):

        def test_properties_and_symmetry(self):
            self.assertEqual(Constants.PI.symbol, 'π')
            self.assertEqual(Constants.e.symbol, 'e')
            self.assertEqual(Constants.GOLDEN_RATIO.symbol, 'φ')

            # test symmetry
            self.assertEqual(Constants.PI, Constants('π'))
            self.assertEqual(Constants.e, Constants('e'))
            self.assertEqual(Constants.GOLDEN_RATIO, Constants('φ'))

            self.assertEqual(Constants.PI, Constants('PI'))
            self.assertEqual(Constants.e, Constants('e'))
            self.assertEqual(Constants.GOLDEN_RATIO, Constants('GOLDEN_RATIO'))

            self.assertEqual(Constants.PI, Constants('Pi'))
            self.assertEqual(Constants.e, Constants("Euler's Number"))
            self.assertEqual(Constants.GOLDEN_RATIO, Constants('Golden Ratio'))

            self.assertEqual(TextEnum.VALUE1.version, 0)
            self.assertEqual(TextEnum.VALUE2.version, 1)
            self.assertEqual(TextEnum.VALUE3.version, 2)
            self.assertEqual(TextEnum.DEFAULT.version, 3)

            self.assertEqual(TextEnum.VALUE1.help,
                             'Some help text about value1.')
            self.assertEqual(TextEnum.VALUE2.help,
                             'Some help text about value2.')
            self.assertEqual(TextEnum.VALUE3.help,
                             'Some help text about value3.')
            self.assertEqual(TextEnum.DEFAULT.help,
                             'Some help text about default.')

            self.assertEqual(TextEnum.VALUE1, TextEnum('VALUE1'))
            self.assertEqual(TextEnum.VALUE2, TextEnum('VALUE2'))
            self.assertEqual(TextEnum.VALUE3, TextEnum('VALUE3'))
            self.assertEqual(TextEnum.DEFAULT, TextEnum('DEFAULT'))

            self.assertEqual(TextEnum.VALUE1, TextEnum('Value1'))
            self.assertEqual(TextEnum.VALUE2, TextEnum('Value2'))
            self.assertEqual(TextEnum.VALUE3, TextEnum('Value3'))
            self.assertEqual(TextEnum.DEFAULT, TextEnum('Default'))

            # test asymmetry
            self.assertRaises(ValueError, TextEnum, 0)
            self.assertRaises(ValueError, TextEnum, 1)
            self.assertRaises(ValueError, TextEnum, 2)
            self.assertRaises(ValueError, TextEnum, 3)

            # test asymmetry
            self.assertRaises(ValueError, TextEnum,
                              'Some help text about value1.')
            self.assertRaises(ValueError, TextEnum,
                              'Some help text about value2.')
            self.assertRaises(ValueError, TextEnum,
                              'Some help text about value3.')
            self.assertRaises(ValueError, TextEnum,
                              'Some help text about default.')

            # test basic case insensitive iterable symmetry
            self.assertEqual(TextEnum.VALUE1, TextEnum('val1'))
            self.assertEqual(TextEnum.VALUE1, TextEnum('v1'))
            self.assertEqual(TextEnum.VALUE1, TextEnum('v one'))
            self.assertEqual(TextEnum.VALUE1, TextEnum('VaL1'))
            self.assertEqual(TextEnum.VALUE1, TextEnum('V1'))
            self.assertEqual(TextEnum.VALUE1, TextEnum('v ONE'))

            self.assertEqual(TextEnum.VALUE2, TextEnum('val22'))
            self.assertEqual(TextEnum.VALUE2, TextEnum('v2'))
            self.assertEqual(TextEnum.VALUE2, TextEnum('v two'))
            self.assertEqual(TextEnum.VALUE2, TextEnum('VaL22'))
            self.assertEqual(TextEnum.VALUE2, TextEnum('V2'))
            self.assertEqual(TextEnum.VALUE2, TextEnum('v TWo'))

            self.assertEqual(TextEnum.VALUE3, TextEnum('val333'))
            self.assertEqual(TextEnum.VALUE3, TextEnum('v3'))
            self.assertEqual(TextEnum.VALUE3, TextEnum('v three'))
            self.assertEqual(TextEnum.VALUE3, TextEnum('VaL333'))
            self.assertEqual(TextEnum.VALUE3, TextEnum('V333'))
            self.assertEqual(TextEnum.VALUE3, TextEnum('v THRee'))

            self.assertEqual(TextEnum.DEFAULT, TextEnum('default'))
            self.assertEqual(TextEnum.DEFAULT, TextEnum('DeFaULT'))
            self.assertEqual(TextEnum.DEFAULT, TextEnum('DEfacTO'))
            self.assertEqual(TextEnum.DEFAULT, TextEnum('defacto'))
            self.assertEqual(TextEnum.DEFAULT, TextEnum('NONE'))
            self.assertEqual(TextEnum.DEFAULT, TextEnum('none'))

        def test_value_type_coercion(self):
            """test basic value coercion from str"""
            self.assertEqual(Constants.PI, Constants(
                '3.14159265358979323846264338327950288'))
            self.assertEqual(Constants.e, Constants('2.71828'))
            self.assertEqual(Constants.GOLDEN_RATIO, Constants(
                '1.61803398874989484820458683436563811'))

            self.assertEqual(SmallPosIntEnum.VAL1, SmallPosIntEnum('0'))
            self.assertEqual(SmallPosIntEnum.VAL2, SmallPosIntEnum('2'))
            self.assertEqual(SmallPosIntEnum.VAL3, SmallPosIntEnum('32767'))

            self.assertEqual(SmallIntEnum.VALn1, SmallIntEnum('-32768'))
            self.assertEqual(SmallIntEnum.VAL0, SmallIntEnum('0'))
            self.assertEqual(SmallIntEnum.VAL1, SmallIntEnum('1'))
            self.assertEqual(SmallIntEnum.VAL2, SmallIntEnum('2'))
            self.assertEqual(SmallIntEnum.VAL3, SmallIntEnum('32767'))

            self.assertEqual(IntEnum.VALn1, IntEnum('-2147483648'))
            self.assertEqual(IntEnum.VAL0, IntEnum('0'))
            self.assertEqual(IntEnum.VAL1, IntEnum('1'))
            self.assertEqual(IntEnum.VAL2, IntEnum('2'))
            self.assertEqual(IntEnum.VAL3, IntEnum('2147483647'))

            self.assertEqual(PosIntEnum.VAL0, PosIntEnum('0'))
            self.assertEqual(PosIntEnum.VAL1, PosIntEnum('1'))
            self.assertEqual(PosIntEnum.VAL2, PosIntEnum('2'))
            self.assertEqual(PosIntEnum.VAL3, PosIntEnum('2147483647'))

            self.assertEqual(BigPosIntEnum.VAL0, BigPosIntEnum('0'))
            self.assertEqual(BigPosIntEnum.VAL1, BigPosIntEnum('1'))
            self.assertEqual(BigPosIntEnum.VAL2, BigPosIntEnum('2'))
            self.assertEqual(BigPosIntEnum.VAL3, BigPosIntEnum('2147483648'))

            self.assertEqual(BigIntEnum.VAL0, BigIntEnum('-2147483649'))
            self.assertEqual(BigIntEnum.VAL1, BigIntEnum('1'))
            self.assertEqual(BigIntEnum.VAL2, BigIntEnum('2'))
            self.assertEqual(BigIntEnum.VAL3, BigIntEnum('2147483648'))

        def test_symmetric_type_coercion(self):
            """test that symmetric properties have types coerced"""
            self.assertEqual(BigIntEnum.VAL0, BigIntEnum(BigPosIntEnum.VAL0))
            self.assertEqual(BigIntEnum.VAL1, BigIntEnum(BigPosIntEnum.VAL1))
            self.assertEqual(BigIntEnum.VAL2, BigIntEnum(BigPosIntEnum.VAL2))
            self.assertEqual(BigIntEnum.VAL3, BigIntEnum(BigPosIntEnum.VAL3))

            self.assertEqual(BigIntEnum.VAL0, BigIntEnum(0))
            self.assertEqual(BigIntEnum.VAL0, BigIntEnum('0'))

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
            tester = EnumTester.objects.create(
                small_pos_int=SmallPosIntEnum.VAL2,
                small_int=SmallIntEnum.VAL0,
                pos_int=PosIntEnum.VAL1,
                int=IntEnum.VALn1,
                big_pos_int=BigPosIntEnum.VAL3,
                big_int=BigIntEnum.VAL2,
                constant=Constants.GOLDEN_RATIO,
                text=TextEnum.VALUE2
            )

            self.assertEqual(tester.small_pos_int, SmallPosIntEnum.VAL2)
            self.assertEqual(tester.small_int, SmallIntEnum.VAL0)
            self.assertEqual(tester.pos_int, PosIntEnum.VAL1)
            self.assertEqual(tester.int, IntEnum.VALn1)
            self.assertEqual(tester.big_pos_int, BigPosIntEnum.VAL3)
            self.assertEqual(tester.big_int, BigIntEnum.VAL2)
            self.assertEqual(tester.constant, Constants.GOLDEN_RATIO)
            self.assertEqual(tester.text, TextEnum.VALUE2)

            tester.small_pos_int = SmallPosIntEnum.VAL1
            tester.small_int = SmallIntEnum.VAL2
            tester.pos_int = PosIntEnum.VAL0
            tester.int = IntEnum.VAL1
            tester.big_pos_int = BigPosIntEnum.VAL2
            tester.big_int = BigIntEnum.VAL1
            tester.constant = Constants.PI
            tester.text = TextEnum.VALUE3

            tester.save()

            self.assertEqual(tester.small_pos_int, SmallPosIntEnum.VAL1)
            self.assertEqual(tester.small_int, SmallIntEnum.VAL2)
            self.assertEqual(tester.pos_int, PosIntEnum.VAL0)
            self.assertEqual(tester.int, IntEnum.VAL1)
            self.assertEqual(tester.big_pos_int, BigPosIntEnum.VAL2)
            self.assertEqual(tester.big_int, BigIntEnum.VAL1)
            self.assertEqual(tester.constant, Constants.PI)
            self.assertEqual(tester.text, TextEnum.VALUE3)

            tester.refresh_from_db()

            self.assertEqual(tester.small_pos_int, SmallPosIntEnum.VAL1)
            self.assertEqual(tester.small_int, SmallIntEnum.VAL2)
            self.assertEqual(tester.pos_int, PosIntEnum.VAL0)
            self.assertEqual(tester.int, IntEnum.VAL1)
            self.assertEqual(tester.big_pos_int, BigPosIntEnum.VAL2)
            self.assertEqual(tester.big_int, BigIntEnum.VAL1)
            self.assertEqual(tester.constant, Constants.PI)
            self.assertEqual(tester.text, TextEnum.VALUE3)

            tester.small_pos_int = '32767'
            tester.small_int = -32768
            tester.pos_int = 2147483647
            tester.int = -2147483648
            tester.big_pos_int = 2147483648
            tester.big_int = -2147483649
            tester.constant = '2.71828'
            tester.text = 'D'

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

            self.assertRaises(
                ValueError,
                EnumChoiceField,
                enum=EmptyEqEnum,
                empty_value=None
            )

            try:
                EnumChoiceField(enum=EmptyEqEnum)
            except Exception:  # pragma: no cover
                self.fail(
                    "EnumChoiceField() raised value error with alternative"
                    "empty_value set."
                )

            class EmptyEqEnum2(TextChoices, s('prop', case_fold=True)):

                A = 'A', ''
                B = 'B', 'ok'

            self.assertRaises(
                ValueError,
                EnumChoiceField,
                enum=EmptyEqEnum2
            )

            try:
                EnumChoiceField(enum=EmptyEqEnum2, empty_value=None)
            except Exception:  # pragma: no cover
                self.fail(
                    "EnumChoiceField() raised value error with alternative"
                    "empty_value set."
                )


    class TestFieldTypeResolutionProps(TestFieldTypeResolution):
        MODEL_CLASS = EnumTester


    class TestEnumQueriesProps(TestEnumQueries):

        MODEL_CLASS = EnumTester

        def test_query(self):
            # don't call super b/c referenced types are different

            self.assertEqual(EnumTester.objects.filter(small_pos_int=self.SmallPosIntEnum.VAL2).count(), 2)
            self.assertEqual(EnumTester.objects.filter(small_pos_int=self.SmallPosIntEnum.VAL2.value).count(), 2)
            self.assertEqual(EnumTester.objects.filter(small_pos_int='Value 2').count(), 2)
            self.assertEqual(EnumTester.objects.filter(small_pos_int=self.SmallPosIntEnum.VAL2.name).count(), 2)

            self.assertEqual(EnumTester.objects.filter(big_pos_int=self.BigPosIntEnum.VAL3).count(), 2)
            self.assertEqual(EnumTester.objects.filter(big_pos_int=self.BigPosIntEnum.VAL3.label).count(), 2)
            self.assertEqual(EnumTester.objects.filter(big_pos_int=None).count(), 1)

            self.assertEqual(EnumTester.objects.filter(constant=self.Constants.GOLDEN_RATIO).count(), 2)
            self.assertEqual(EnumTester.objects.filter(constant=self.Constants.GOLDEN_RATIO.name).count(), 2)
            self.assertEqual(EnumTester.objects.filter(constant=Constants.GOLDEN_RATIO.value).count(), 2)
            self.assertEqual(EnumTester.objects.filter(constant__isnull=True).count(), 1)

            # test symmetry
            self.assertEqual(EnumTester.objects.filter(constant=Constants.GOLDEN_RATIO.symbol).count(), 2)
            self.assertEqual(EnumTester.objects.filter(constant='φ').count(), 2)

            self.assertEqual(EnumTester.objects.filter(text=TextEnum.VALUE2).count(), 2)
            self.assertEqual(len(TextEnum.VALUE2.aliases), 3)
            for alias in TextEnum.VALUE2.aliases:
                self.assertEqual(EnumTester.objects.filter(text=alias).count(), 2)

            self.assertRaises(ValueError, EnumTester.objects.filter, int_field='a')
            self.assertRaises(ValueError, EnumTester.objects.filter, float_field='a')
            self.assertRaises(ValueError, EnumTester.objects.filter, constant='p')
            self.assertRaises(ValueError, EnumTester.objects.filter, big_pos_int='p')
            self.assertRaises(ValueError, EnumTester.objects.filter, big_pos_int=type('WrongType')())


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
                'big_pos_int': 'Value 2147483647',
                'big_int': 'VAL2',
                'constant': 'φ',
                'text': 'V TWo',
                'dj_int_enum': 3,
                'dj_text_enum': self.DJTextEnum.A,
                'non_strict_int': 15
            }

        @property
        def update_params(self):
            return {
                'non_strict_int': 100,
                'constant': 'π',
                'big_int': -2147483649
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
                'dj_int_enum': 2,
                'dj_text_enum': 'B',
                'non_strict_int': self.SmallPosIntEnum.VAL2
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
                'dj_int_enum': '',
                'dj_text_enum': 'D',
                'non_strict_int': 'Not an int'
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
                'constant': self.Constants.GOLDEN_RATIO,
                'text': self.TextEnum.VALUE2,
                'dj_int_enum': self.DJIntEnum.TWO,
                'dj_text_enum': self.DJTextEnum.C,
                'non_strict_int': self.SmallPosIntEnum.VAL1
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
                'constant': 'φ',
                'text': 'v two',
                'dj_int_enum': self.DJIntEnum.TWO,
                'dj_text_enum': self.DJTextEnum.C,
                'non_strict_int': 150
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
                'dj_int_enum': ['value'],
                'dj_text_enum': ['value'],
                'non_strict_int': ['value', 'name', 'label'],
            }

        if DJANGO_FILTERS_INSTALLED:
            def test_django_filter(self):
                self.do_test_django_filter(
                    reverse(f'{self.NAMESPACE}:enum-filter-symmetric')
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

        def test_makemigrate_2(self):
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
                    settings.TEST_MIGRATION_DIR / '0004_remove_int_enum.py')
            )

            call_command('makemigrations', name='remove_int_enum')

            # should not exist!
            self.assertTrue(
                os.path.isfile(
                    settings.TEST_MIGRATION_DIR / '0004_remove_int_enum.py')
            )

        def test_makemigrate_6(self):
            from django.conf import settings
            set_models(6)
            self.assertFalse(
                os.path.isfile(
                    settings.TEST_MIGRATION_DIR / '0005_add_int_enum.py')
            )

            call_command('makemigrations', name='add_int_enum')

            # should not exist!
            self.assertTrue(
                os.path.isfile(
                    settings.TEST_MIGRATION_DIR / '0005_add_int_enum.py')
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

            MigrationTesterOld = self.old_state.apps.get_model(
                'django_enum_tests_edit_tests',
                'MigrationTester'
            )
            MigrationTesterNew = self.new_state.apps.get_model(
                'django_enum_tests_edit_tests',
                'MigrationTester'
            )

            for value in reversed(
                    MigrationTesterOld._meta.get_field('int_enum').choices
            ):
                for obj in MigrationTesterNew.objects.filter(
                        int_enum=value[0]):
                    obj.int_enum = value[0] + 1
                    obj.save()

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

            MigrationTesterOld = self.old_state.apps.get_model(
                'django_enum_tests_edit_tests',
                'MigrationTester'
            )

            MigrationTesterOld.objects.filter(color='K').delete()

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

        def test_rename_names_code(self):
            # no migration was generated for this model class change
            set_models(4)
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
        migrate_to = ('django_enum_tests_edit_tests', '0004_remove_int_enum')

        @classmethod
        def setUpClass(cls):
            set_models(5)
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

        def test_0004_remove_int_enum(self):
            from django.core.exceptions import FieldDoesNotExist, FieldError

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

        def test_0004_code(self):
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

        migrate_from = ('django_enum_tests_edit_tests', '0004_remove_int_enum')
        migrate_to = ('django_enum_tests_edit_tests', '0005_add_int_enum')

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
            for color in ['R', 'G', 'B']:
                MigrationTester.objects.create(color=color)

        def test_0005_add_int_enum(self):
            from django.core.exceptions import FieldDoesNotExist, FieldError

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
                MigrationTesterNew.objects.filter(int_enum=0).count(), 0)
            self.assertEqual(
                MigrationTesterNew.objects.filter(int_enum=1).count(), 0)
            self.assertEqual(
                MigrationTesterNew.objects.filter(int_enum=2).count(), 0)
            self.assertEqual(
                MigrationTesterNew.objects.filter(int_enum=3).count(), 0)

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

        def test_0005_code(self):
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
                'big_pos_int': 'Value 2147483647',
                'big_int': 'VAL2',
                'constant': 'φ',
                'text': 'V TWo'
            }

        @property
        def values_params(self):
            return {
                'small_pos_int': self.SmallPosIntEnum.VAL2,
                'small_int': 'Value -32768',
                'pos_int': 2147483647,
                'int': -2147483648,
                'big_pos_int': 'Value 2147483647',
                'big_int': 'VAL2',
                'constant': 'φ',
                'text': 'V TWo',
                'dj_int_enum': 3,
                'dj_text_enum': self.DJTextEnum.A,
                'non_strict_int': 75
            }

        def test_values(self):
            from django.db.models.fields import NOT_PROVIDED
            values1, values2 = super().test_values()

            # also test equality symmetry
            self.assertEqual(values1['small_pos_int'], 'Value 2')
            self.assertEqual(values1['small_int'], 'Value -32768')
            self.assertEqual(values1['pos_int'], 2147483647)
            self.assertEqual(values1['int'], -2147483648)
            self.assertEqual(values1['big_pos_int'], 'Value 2147483647')
            self.assertEqual(values1['big_int'], 'VAL2')
            self.assertEqual(values1['constant'], 'φ')
            self.assertEqual(values1['text'], 'V TWo')

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
            tester = super().test_validate()

            self.assertTrue(tester._meta.get_field('small_int').validate('Value -32768', tester) is None)
            self.assertTrue(tester._meta.get_field('pos_int').validate(2147483647, tester) is None)
            self.assertTrue(tester._meta.get_field('int').validate('VALn1', tester) is None)
            self.assertTrue(tester._meta.get_field('big_pos_int').validate('Value 2147483647', tester) is None)
            self.assertTrue(tester._meta.get_field('big_int').validate(self.BigPosIntEnum.VAL2, tester) is None)
            self.assertTrue(tester._meta.get_field('constant').validate('φ', tester) is None)
            self.assertTrue(tester._meta.get_field('text').validate('default', tester) is None)

            self.assertTrue(tester._meta.get_field('dj_int_enum').validate(1, tester) is None)
            self.assertTrue(tester._meta.get_field('dj_text_enum').validate('A', tester) is None)
            self.assertTrue(tester._meta.get_field('non_strict_int').validate(20, tester) is None)

    class PerformanceTest(TestCase):  # pragma: no cover

        COUNT = 10000

        def test_save_performance(self):
            enum_start = perf_counter()
            for idx in range(0, self.COUNT):
                EnumTester.objects.create(
                    small_pos_int=SmallPosIntEnum.VAL2,
                    small_int='Value -32768',
                    pos_int=2147483647,
                    int=-2147483648,
                    big_pos_int='Value 2147483647',
                    big_int='VAL2',
                    constant='φ',
                    text='V TWo',
                    dj_int_enum=3,
                    dj_text_enum=DJTextEnum.A,
                    non_strict_int=15
                )
            enum_stop = perf_counter()

            choice_start = perf_counter()
            for idx in range(0, self.COUNT):
                PerfCompare.objects.create(
                    small_pos_int=2,
                    small_int=-32768,
                    pos_int=2147483647,
                    int=-2147483648,
                    big_pos_int=2147483647,
                    big_int=2,
                    constant=1.61803398874989484820458683436563811,
                    text='V22',
                    dj_int_enum=3,
                    dj_text_enum='A',
                    non_strict_int=15
                )
            choice_stop = perf_counter()

            enum_direct_start = perf_counter()
            for idx in range(0, self.COUNT):
                EnumTester.objects.create(
                    small_pos_int=SmallPosIntEnum.VAL2,
                    small_int=SmallIntEnum.VALn1,
                    pos_int=PosIntEnum.VAL3,
                    int=IntEnum.VALn1,
                    big_pos_int=BigPosIntEnum.VAL3,
                    big_int=BigIntEnum.VAL2,
                    constant=Constants.GOLDEN_RATIO,
                    text=TextEnum.VALUE2,
                    dj_int_enum=DJIntEnum.THREE,
                    dj_text_enum=DJTextEnum.A,
                    non_strict_int=15
                )
            enum_direct_stop = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start
            enum_direct_time = enum_direct_stop - enum_direct_start
            # flag if performance degrades signficantly - running about 2x for big lookups
            self.assertTrue((enum_time / choice_time) < 3)
            # print(f'{enum_time} {enum_direct_time} {choice_time}')

        def test_read_performance(self):

            for idx in range(0, self.COUNT):
                EnumTester.objects.create(
                    small_pos_int=SmallPosIntEnum.VAL2,
                    small_int=SmallIntEnum.VALn1,
                    pos_int=PosIntEnum.VAL3,
                    int=IntEnum.VALn1,
                    big_pos_int=BigPosIntEnum.VAL3,
                    big_int=BigIntEnum.VAL2,
                    constant=Constants.GOLDEN_RATIO,
                    text=TextEnum.VALUE2,
                    dj_int_enum=DJIntEnum.THREE,
                    dj_text_enum=DJTextEnum.A,
                    non_strict_int=15
                )

            for idx in range(0, self.COUNT):
                PerfCompare.objects.create(
                    small_pos_int=2,
                    small_int=-32768,
                    pos_int=2147483647,
                    int=-2147483648,
                    big_pos_int=2147483647,
                    big_int=2,
                    constant=1.61803398874989484820458683436563811,
                    text='V22',
                    dj_int_enum=3,
                    dj_text_enum='A',
                    non_strict_int=15
                )

            self.assertEqual(EnumTester.objects.count(), self.COUNT)
            self.assertEqual(PerfCompare.objects.count(), self.COUNT)

            enum_start = perf_counter()
            for _ in EnumTester.objects.all():
                continue
            enum_stop = perf_counter()

            choice_start = perf_counter()
            for _ in PerfCompare.objects.all():
                continue
            choice_stop = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start
            self.assertTrue((enum_time / choice_time) < 7)
            # print(f'{enum_time} {choice_time}')

        def test_single_field_perf_diff(self):

            enum_start = perf_counter()
            for idx in range(0, self.COUNT):
                SingleEnumPerf.objects.create(small_pos_int=0)
            enum_stop = perf_counter()

            choice_start = perf_counter()
            for idx in range(0, self.COUNT):
                SingleFieldPerf.objects.create(small_pos_int=0)
            choice_stop = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start

            # Enum tends to be about ~12% slower
            self.assertTrue((enum_time / choice_time) < 1.5)
            # print(f'{enum_time} {choice_time}')

            enum_start = perf_counter()
            for _ in SingleEnumPerf.objects.all():
                continue
            enum_stop = perf_counter()

            choice_start = perf_counter()
            for _ in SingleFieldPerf.objects.all():
                continue
            choice_stop = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start

            # print(f'{enum_time} {choice_time}')
            # tends to be about 1.8x slower
            self.assertTrue((enum_time / choice_time) < 2.5)

else:  # pragma: no cover
    pass
