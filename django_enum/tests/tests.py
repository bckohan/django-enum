from pathlib import Path

from bs4 import BeautifulSoup as Soup
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import Client, TestCase
from django.urls import reverse
from django_enum import TextChoices
from django_enum.tests.app1.enums import (
    BigIntEnum,
    BigPosIntEnum,
    Constants,
    IntEnum,
    PosIntEnum,
    PrecedenceTest,
    SmallIntEnum,
    SmallPosIntEnum,
    TextEnum,
    DJIntEnum,
    DJTextEnum
)
from django_enum.tests.app1.models import EnumTester, MyModel
from enum_properties import s
from django.test import TestCase
from django.core.management import call_command
import os
from django_test_migrations.constants import MIGRATION_TEST_MARKER
from django_test_migrations.contrib.unittest_case import MigratorTestCase


def set_models(version):
    from importlib import reload
    from django.conf import settings
    from shutil import copyfile
    from .edit_tests import models
    import warnings
    copyfile(
        settings.TEST_EDIT_DIR / f'_{version}.py',
        settings.TEST_MIGRATION_DIR.parent / 'models.py'
    )
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        reload(models)


APP1_DIR = Path(__file__).parent / 'app1'


class TestChoices(TestCase):
    """Test that Django's choices types work as expected"""

    def setUp(self):
        pass

    def test_integer_choices(self):

        EnumTester.objects.create(dj_int_enum=DJIntEnum.ONE)
        EnumTester.objects.create(dj_int_enum=DJIntEnum.TWO)
        EnumTester.objects.create(dj_int_enum=DJIntEnum.THREE)

        for obj in EnumTester.objects.all():
            self.assertIsInstance(obj.dj_int_enum, DJIntEnum)

        self.assertEqual(EnumTester.objects.filter(dj_int_enum='1').count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=1).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=DJIntEnum.ONE).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=DJIntEnum(1)).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=DJIntEnum['ONE']).count(), 1)

        self.assertEqual(EnumTester.objects.filter(dj_int_enum='2').count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=2).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=DJIntEnum.TWO).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=DJIntEnum(2)).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=DJIntEnum['TWO']).count(), 1)

        self.assertEqual(EnumTester.objects.filter(dj_int_enum='3').count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=3).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=DJIntEnum.THREE).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=DJIntEnum(3)).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_int_enum=DJIntEnum['THREE']).count(), 1)

        EnumTester.objects.all().delete()

    def test_text_choices(self):

        EnumTester.objects.create(dj_text_enum=DJTextEnum.A)
        EnumTester.objects.create(dj_text_enum=DJTextEnum.B)
        EnumTester.objects.create(dj_text_enum=DJTextEnum.C)

        for obj in EnumTester.objects.all():
            self.assertIsInstance(obj.dj_text_enum, DJTextEnum)

        self.assertEqual(EnumTester.objects.filter(dj_text_enum='A').count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_text_enum=DJTextEnum.A).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_text_enum=DJTextEnum('A')).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_text_enum=DJTextEnum['A']).count(), 1)

        self.assertEqual(EnumTester.objects.filter(dj_text_enum='B').count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_text_enum=DJTextEnum.B).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_text_enum=DJTextEnum('B')).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_text_enum=DJTextEnum['B']).count(), 1)

        self.assertEqual(EnumTester.objects.filter(dj_text_enum='C').count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_text_enum=DJTextEnum.C).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_text_enum=DJTextEnum('C')).count(), 1)
        self.assertEqual(EnumTester.objects.filter(dj_text_enum=DJTextEnum['C']).count(), 1)

        EnumTester.objects.all().delete()


class TestDjangoEnums(TestCase):

    def setUp(self):
        pass

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

        self.assertEqual(TextEnum.VALUE1.help, 'Some help text about value1.')
        self.assertEqual(TextEnum.VALUE2.help, 'Some help text about value2.')
        self.assertEqual(TextEnum.VALUE3.help, 'Some help text about value3.')
        self.assertEqual(TextEnum.DEFAULT.help, 'Some help text about default.')

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
        self.assertRaises(ValueError, TextEnum, 'Some help text about value1.')
        self.assertRaises(ValueError, TextEnum, 'Some help text about value2.')
        self.assertRaises(ValueError, TextEnum, 'Some help text about value3.')
        self.assertRaises(ValueError, TextEnum, 'Some help text about default.')

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
        self.assertEqual(Constants.PI, Constants('3.14159265358979323846264338327950288'))
        self.assertEqual(Constants.e, Constants('2.71828'))
        self.assertEqual(Constants.GOLDEN_RATIO, Constants('1.61803398874989484820458683436563811'))

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

    def test_base_fields(self):
        """
        Test that the Enum metaclass picks the correct database field type for each enum.
        """
        tester = EnumTester.objects.create()
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

    def test_saving(self):
        """
        Test that the Enum metaclass picks the correct database field type for each enum.
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
            #self.assertRaises(ValidationError, tester.save)
        tester.refresh_from_db()

        with transaction.atomic():
            tester.char_choice = 5
            tester.save()
            #self.assertRaises(ValueError, tester.save)
        tester.refresh_from_db()

        with transaction.atomic():
            tester.int_choice = 5
            tester.save()
            #self.assertRaises(ValueError, tester.save)
        tester.refresh_from_db()
        #####################################################################################

        with transaction.atomic():
            tester.int_choice = 'a'
            self.assertRaises(ValueError, tester.save)
        tester.refresh_from_db()

        tester.text = None
        tester.save()
        self.assertEqual(tester.text, None)

    def test_serialization(self):
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

        serialized = serializers.serialize('json', EnumTester.objects.all())

        tester.delete()

        for mdl in serializers.deserialize('json', serialized):
            mdl.save()
            tester = mdl.object

        self.assertEqual(tester.small_pos_int, SmallPosIntEnum.VAL2)
        self.assertEqual(tester.small_int, SmallIntEnum.VAL0)
        self.assertEqual(tester.pos_int, PosIntEnum.VAL1)
        self.assertEqual(tester.int, IntEnum.VALn1)
        self.assertEqual(tester.big_pos_int, BigPosIntEnum.VAL3)
        self.assertEqual(tester.big_int, BigIntEnum.VAL2)
        self.assertEqual(tester.constant, Constants.GOLDEN_RATIO)
        self.assertEqual(tester.text, TextEnum.VALUE2)

    def test_validate(self):
        tester = EnumTester.objects.create()
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
        self.assertTrue(tester._meta.get_field('small_int').validate('Value -32768', tester) is None)
        self.assertTrue(tester._meta.get_field('pos_int').validate(2147483647, tester) is None)
        self.assertTrue(tester._meta.get_field('int').validate('VALn1', tester) is None)
        self.assertTrue(tester._meta.get_field('big_pos_int').validate('Value 2147483647', tester) is None)
        self.assertTrue(tester._meta.get_field('big_int').validate(BigPosIntEnum.VAL2, tester) is None)
        self.assertTrue(tester._meta.get_field('constant').validate('φ', tester) is None)
        self.assertTrue(tester._meta.get_field('text').validate('default', tester) is None)

    def test_clean(self):

        tester = EnumTester(
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


class TestEnumQueries(TestCase):

    def setUp(self):
        EnumTester.objects.all().delete()

    def test_query(self):
        EnumTester.objects.create(
            small_pos_int=SmallPosIntEnum.VAL2,
            small_int=SmallIntEnum.VAL0,
            pos_int=PosIntEnum.VAL1,
            int=IntEnum.VALn1,
            big_pos_int=BigPosIntEnum.VAL3,
            big_int=BigIntEnum.VAL2,
            constant=Constants.GOLDEN_RATIO,
            text=TextEnum.VALUE2
        )
        EnumTester.objects.create(
            small_pos_int=SmallPosIntEnum.VAL2,
            small_int=SmallIntEnum.VAL0,
            pos_int=PosIntEnum.VAL1,
            int=IntEnum.VALn1,
            big_pos_int=BigPosIntEnum.VAL3,
            big_int=BigIntEnum.VAL2,
            constant=Constants.GOLDEN_RATIO,
            text=TextEnum.VALUE2
        )

        EnumTester.objects.create()

        self.assertEqual(EnumTester.objects.filter(small_pos_int=SmallPosIntEnum.VAL2).count(), 2)
        self.assertEqual(EnumTester.objects.filter(small_pos_int=SmallPosIntEnum.VAL2.value).count(), 2)
        self.assertEqual(EnumTester.objects.filter(small_pos_int='Value 2').count(), 2)
        self.assertEqual(EnumTester.objects.filter(small_pos_int=SmallPosIntEnum.VAL2.name).count(), 2)

        self.assertEqual(EnumTester.objects.filter(big_pos_int=BigPosIntEnum.VAL3).count(), 2)
        self.assertEqual(EnumTester.objects.filter(big_pos_int=BigPosIntEnum.VAL3.label).count(), 2)
        self.assertEqual(EnumTester.objects.filter(big_pos_int=None).count(), 1)

        self.assertEqual(EnumTester.objects.filter(constant=Constants.GOLDEN_RATIO).count(), 2)
        self.assertEqual(EnumTester.objects.filter(constant=Constants.GOLDEN_RATIO.name).count(), 2)
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


class TestRequests(TestCase):

    objects = []
    values = {
        val: {} for val in [
            'small_pos_int',
            'small_int',
            'pos_int',
            'int',
            'big_pos_int',
            'big_int',
            'constant',
            'text'
        ]
    }

    def setUp(self):
        EnumTester.objects.all().delete()
        self.objects.append(
            EnumTester.objects.create()
        )
        self.objects.append(
            EnumTester.objects.create(
                small_pos_int=SmallPosIntEnum.VAL1,
                small_int=SmallIntEnum.VAL1,
                pos_int=PosIntEnum.VAL1,
                int=IntEnum.VAL1,
                big_pos_int=BigPosIntEnum.VAL1,
                big_int=BigIntEnum.VAL1,
                constant=Constants.PI,
                text=TextEnum.VALUE1
            )
        )
        for _ in range(0, 2):
            self.objects.append(
                EnumTester.objects.create(
                    small_pos_int=SmallPosIntEnum.VAL2,
                    small_int=SmallIntEnum.VAL2,
                    pos_int=PosIntEnum.VAL2,
                    int=IntEnum.VAL2,
                    big_pos_int=BigPosIntEnum.VAL2,
                    big_int=BigIntEnum.VAL2,
                    constant=Constants.e,
                    text=TextEnum.VALUE2
                )
            )
        for _ in range(0, 3):
            self.objects.append(
                EnumTester.objects.create(
                    small_pos_int=SmallPosIntEnum.VAL3,
                    small_int=SmallIntEnum.VAL3,
                    pos_int=PosIntEnum.VAL3,
                    int=IntEnum.VAL3,
                    big_pos_int=BigPosIntEnum.VAL3,
                    big_int=BigIntEnum.VAL3,
                    constant=Constants.GOLDEN_RATIO,
                    text=TextEnum.VALUE3
                )
            )

        for obj in self.objects:
            for attr in self.values.keys():
                self.values[attr].setdefault(getattr(obj, attr), [])
                self.values[attr][getattr(obj, attr)].append(obj.pk)

    def test_post(self):
        c = Client()
        response = c.post(
            reverse('django_enum_tests_app1:enum-add'),
            {
                'small_pos_int': SmallPosIntEnum.VAL2,
                'small_int': SmallIntEnum.VAL0,
                'pos_int': PosIntEnum.VAL1,
                'int': IntEnum.VALn1,
                'big_pos_int': BigPosIntEnum.VAL3,
                'big_int': BigIntEnum.VAL2,
                'constant': Constants.GOLDEN_RATIO,
                'text': TextEnum.VALUE2,
                'dj_int_enum': DJIntEnum.TWO,
                'dj_text_enum': DJTextEnum.C
            },
            follow=True
        )
        soup = Soup(response.content, features='html.parser')

        added = soup.find_all('div', class_='enum')[-1]
        self.assertEqual(
            SmallPosIntEnum(added.find(class_="small_pos_int").find("span", class_="value").text),
            SmallPosIntEnum.VAL2
        )
        self.assertEqual(
            SmallIntEnum(added.find(class_="small_int").find("span", class_="value").text),
            SmallIntEnum.VAL0
        )
        self.assertEqual(
            PosIntEnum(added.find(class_="pos_int").find("span", class_="value").text),
            PosIntEnum.VAL1
        )
        self.assertEqual(
            IntEnum(added.find(class_="int").find("span", class_="value").text),
            IntEnum.VALn1
        )
        self.assertEqual(
            BigPosIntEnum(added.find(class_="big_pos_int").find("span", class_="value").text),
            BigPosIntEnum.VAL3
        )
        self.assertEqual(
            BigIntEnum(added.find(class_="big_int").find("span", class_="value").text),
            BigIntEnum.VAL2
        )
        self.assertEqual(
            Constants(added.find(class_="constant").find("span", class_="value").text),
            Constants.GOLDEN_RATIO
        )
        self.assertEqual(
            TextEnum(added.find(class_="text").find("span", class_="value").text),
            TextEnum.VALUE2
        )
        self.assertEqual(
            DJIntEnum(int(added.find(class_="dj_int_enum").find("span", class_="value").text)),
            DJIntEnum.TWO
        )
        self.assertEqual(
            DJTextEnum(added.find(class_="dj_text_enum").find("span", class_="value").text),
            DJTextEnum.C
        )
        EnumTester.objects.last().delete()

    def test_add_form(self):
        c = Client()
        response = c.get(reverse('django_enum_tests_app1:enum-add'))
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
        ]:
            field = EnumTester._meta.get_field(field)
            expected = dict(zip(field.enum.values, field.enum.labels))  # value -> label
            null_opt = False
            for option in soup.find('select', id=f'id_{field.name}').find_all('option'):
                if (option['value'] is None or option['value'] == '') and option.text.count('-') >= 2:
                    self.assertTrue(field.blank or field.null)
                    null_opt = True
                    continue

                try:
                    self.assertEqual(str(expected[field.enum(option['value']).value]), option.text)
                    del expected[field.enum(option['value'])]
                except KeyError:  # pragma: no cover
                    self.fail(f'{field.name} did not expect option {option["value"]}: {option.text}.')

            self.assertEqual(len(expected), 0)

            if not field.null and not field.blank:
                self.assertFalse(null_opt, "An unexpected null option is present")  # pragma: no cover

    def test_update_form(self):
        c = Client()
        # test normal choice field and our EnumChoiceField
        for form_url in ['enum-update', 'enum-form-update']:
            for obj in self.objects:
                response = c.get(reverse(f'django_enum_tests_app1:{form_url}', kwargs={'pk': obj.pk}))
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
                ]:
                    field = EnumTester._meta.get_field(field)
                    expected = dict(zip(field.enum.values, field.enum.labels))  # value -> label
                    null_opt = False
                    for option in soup.find('select', id=f'id_{field.name}').find_all('option'):

                        if (option['value'] is None or option['value'] == '') and option.text.count('-') >= 2:
                            self.assertTrue(field.blank or field.null)
                            null_opt = True
                            if option.has_attr('selected'):
                                self.assertIsNone(getattr(obj, field.name))
                            continue

                        try:
                            enum = field.enum(option['value'])
                            self.assertEqual(str(expected[enum.value]), option.text)
                            if option.has_attr('selected'):
                                self.assertEqual(getattr(obj, field.name), enum)
                            del expected[enum.value]
                        except KeyError:  # pragma: no cover
                            self.fail(f'{field.name} did not expect option {option["value"]}: {option.text}.')

                    self.assertEqual(len(expected), 0)

                    if not field.null and not field.blank:
                        self.assertFalse(null_opt, "An unexpected null option is present")  # pragma: no cover


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
        from django.conf import settings
        for migration in [
            settings.TEST_MIGRATION_DIR / '0001_initial.py',
            settings.TEST_MIGRATION_DIR / '0002_alter_values.py',
            settings.TEST_MIGRATION_DIR / '0003_remove_black.py',
            settings.TEST_MIGRATION_DIR / '0004_remove_int_enum.py',
            settings.TEST_MIGRATION_DIR / '0005_add_int_enum.py'
        ]:
            if os.path.exists(migration):  # pragma: no cover
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
            os.path.isfile(settings.TEST_MIGRATION_DIR / '0002_alter_values.py')
        )

        call_command('makemigrations', name='alter_values')

        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / '0002_alter_values.py')
        )

    def test_makemigrate_3(self):
        from django.conf import settings
        set_models(3)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / '0003_remove_black.py')
        )

        call_command('makemigrations', name='remove_black')

        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / '0003_remove_black.py')
        )

    def test_makemigrate_4(self):
        from django.conf import settings
        set_models(4)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / '0004_change_names.py')
        )

        call_command('makemigrations', name='change_names')

        # should not exist!
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / '0004_change_names.py')
        )

    def test_makemigrate_5(self):
        from django.conf import settings
        set_models(5)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / '0004_remove_int_enum.py')
        )

        call_command('makemigrations', name='remove_int_enum')

        # should not exist!
        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / '0004_remove_int_enum.py')
        )

    def test_makemigrate_6(self):
        from django.conf import settings
        set_models(6)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / '0005_add_int_enum.py')
        )

        call_command('makemigrations', name='add_int_enum')

        # should not exist!
        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / '0005_add_int_enum.py')
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
        self.assertEqual(MigrationTester.objects.filter(int_enum=0).count(), 2)
        self.assertEqual(MigrationTester.objects.filter(int_enum=1).count(), 1)
        self.assertEqual(MigrationTester.objects.filter(int_enum=2).count(), 1)

        self.assertEqual(MigrationTester.objects.filter(color='R').count(), 1)
        self.assertEqual(MigrationTester.objects.filter(color='G').count(), 1)
        self.assertEqual(MigrationTester.objects.filter(color='B').count(), 1)
        self.assertEqual(MigrationTester.objects.filter(color='K').count(), 1)

    def test_0001_code(self):
        from .edit_tests.models import MigrationTester

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (MigrationTester.IntEnum(0), MigrationTester.Color((1,0,0))),
            (MigrationTester.IntEnum['TWO'], MigrationTester.Color('00FF00')),
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
            for obj in MigrationTesterNew.objects.filter(int_enum=value[0]):
                obj.int_enum = value[0] + 1
                obj.save()

        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=0).count(), 0)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=1).count(), 2)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=2).count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=3).count(), 1)

        self.assertEqual(MigrationTesterNew.objects.filter(color='R').count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color='G').count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color='B').count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color='K').count(), 1)

    def test_0002_code(self):
        from .edit_tests.models import MigrationTester

        MigrationTester.objects.all().delete()

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (MigrationTester.IntEnum(1), MigrationTester.Color((1, 0, 0))),
            (MigrationTester.IntEnum['TWO'], MigrationTester.Color('00FF00')),
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

        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=0).count(), 0)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=1).count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=2).count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=3).count(), 1)

        self.assertEqual(MigrationTesterNew.objects.filter(color='R').count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color='G').count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color='B').count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color='K').count(), 0)

    def test_0003_code(self):
        from .edit_tests.models import MigrationTester

        MigrationTester.objects.all().delete()

        self.assertFalse(hasattr(MigrationTester.Color, 'BLACK'))

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (MigrationTester.IntEnum(1), MigrationTester.Color((1, 0, 0))),
            (MigrationTester.IntEnum['TWO'], MigrationTester.Color('00FF00')),
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
            (MigrationTester.IntEnum['THREE'], MigrationTester.Color('0000ff')),
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
            MigrationTester.objects.count(),
            3
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
            MigrationTesterNew.objects.filter(int_enum__isnull=True).count(),
            3
        )

        MigrationTesterNew.objects.filter(color='R').update(int_enum='A')
        MigrationTesterNew.objects.filter(color='G').update(int_enum='B')
        MigrationTesterNew.objects.filter(color='B').update(int_enum='C')

        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=0).count(), 0)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=1).count(), 0)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=2).count(), 0)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=3).count(), 0)

        self.assertEqual(MigrationTesterNew.objects.filter(int_enum='A').count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum='B').count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum='C').count(), 1)

        self.assertEqual(MigrationTesterNew.objects.filter(color='R').count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color='G').count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color='B').count(), 1)

    def test_0005_code(self):
        from .edit_tests.models import MigrationTester

        MigrationTester.objects.all().delete()

        for int_enum, color in [
            (MigrationTester.IntEnum.A, MigrationTester.Color.RED),
            (MigrationTester.IntEnum('B'), MigrationTester.Color('Green')),
            (MigrationTester.IntEnum['C'], MigrationTester.Color('0000ff')),
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

        MigrationTester.objects.all().delete()


def test_migration_test_marker_tag():
    """Ensure ``MigratorTestCase`` sublasses are properly tagged."""
    assert MIGRATION_TEST_MARKER in TestInitialMigration.tags
    assert MIGRATION_TEST_MARKER in TestAlterValuesMigration.tags
    assert MIGRATION_TEST_MARKER in TestRemoveBlackMigration.tags
    assert MIGRATION_TEST_MARKER in TestRemoveIntEnumMigration.tags
    assert MIGRATION_TEST_MARKER in TestAddIntEnumMigration.tags
