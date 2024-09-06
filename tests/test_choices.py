import pytest
from importlib.util import find_spec
from tests.utils import EnumTypeMixin, IGNORE_ORA_01843
from django.test import TestCase
from django.db import connection
from django.db.models import Q
from django.db.utils import DatabaseError
from tests.djenum.models import BadDefault
from django.test.utils import CaptureQueriesContext
from django.core import serializers
from django.core.exceptions import ValidationError
from tests.djenum.models import EnumTester


class TestChoices(EnumTypeMixin, TestCase):
    """Test that Django's choices types work as expected"""

    MODEL_CLASS = EnumTester

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
            "extern": self.ExternEnum.THREE,
            "date_enum": self.DateEnum.HUGO,
            "datetime_enum": self.DateTimeEnum.PINATUBO,
            "duration_enum": self.DurationEnum.DAY,
            "time_enum": self.TimeEnum.LUNCH,
            "decimal_enum": self.DecimalEnum.FOUR,
        }

    def test_defaults(self):
        from django.db.models import NOT_PROVIDED

        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("small_pos_int").get_default(), None
        )

        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("small_int").get_default(),
            self.enum_type("small_int").VAL3,
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("small_int").get_default(),
            self.enum_type("small_int"),
        )

        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("pos_int").get_default(),
            self.enum_type("pos_int").VAL3,
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("pos_int").get_default(),
            self.enum_type("pos_int"),
        )

        self.assertEqual(self.MODEL_CLASS._meta.get_field("int").get_default(), None)
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("big_pos_int").get_default(), None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("big_int").get_default(),
            self.enum_type("big_int").VAL0,
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("big_int").get_default(),
            self.enum_type("big_int"),
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("constant").get_default(), None
        )
        self.assertEqual(self.MODEL_CLASS._meta.get_field("text").get_default(), None)
        self.assertEqual(self.MODEL_CLASS._meta.get_field("extern").get_default(), None)
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("date_enum").get_default(),
            self.enum_type("date_enum").EMMA,
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("datetime_enum").get_default(), None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("duration_enum").get_default(), None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("time_enum").get_default(), None
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("decimal_enum").get_default(),
            self.enum_type("decimal_enum").THREE,
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("dj_int_enum").get_default(),
            self.enum_type("dj_int_enum").ONE,
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("dj_int_enum").get_default(),
            self.enum_type("dj_int_enum"),
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("dj_text_enum").get_default(),
            self.enum_type("dj_text_enum").A,
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("dj_text_enum").get_default(),
            self.enum_type("dj_text_enum"),
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("non_strict_int").get_default(), 5
        )
        self.assertIsInstance(
            self.MODEL_CLASS._meta.get_field("non_strict_int").get_default(),
            self.enum_primitive("non_strict_int"),
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("non_strict_text").get_default(), ""
        )
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("no_coerce").get_default(), None
        )

        self.assertEqual(BadDefault._meta.get_field("non_strict_int").get_default(), 5)

        self.assertRaises(ValueError, BadDefault.objects.create)

    def test_basic_save(self):
        self.MODEL_CLASS.objects.all().delete()
        try:
            self.MODEL_CLASS.objects.create(**self.create_params)
        except DatabaseError as err:
            print(str(err))
            if (
                IGNORE_ORA_01843
                and connection.vendor == "oracle"
                and "ORA-01843" in str(err)
            ):
                # this is an oracle bug - intermittent failure on
                # perfectly fine date format in SQL
                # TODO - remove when fixed
                pytest.skip("Oracle bug ORA-01843 encountered - skipping")
                return
            raise
        for param in self.fields:
            value = self.create_params.get(
                param, self.MODEL_CLASS._meta.get_field(param).get_default()
            )
            self.assertEqual(
                self.MODEL_CLASS.objects.filter(**{param: value}).count(), 1
            )
        self.MODEL_CLASS.objects.all().delete()

    def test_coerce_to_primitive(self):
        create_params = {**self.create_params, "no_coerce": "32767"}

        try:
            tester = self.MODEL_CLASS.objects.create(**create_params)
        except DatabaseError as err:
            print(str(err))
            if (
                IGNORE_ORA_01843
                and connection.vendor == "oracle"
                and "ORA-01843" in str(err)
            ):
                # this is an oracle bug - intermittent failure on
                # perfectly fine date format in SQL
                # TODO - remove when fixed
                pytest.skip("Oracle bug ORA-01843 encountered - skipping")
                return
            raise

        self.assertIsInstance(tester.no_coerce, int)
        self.assertEqual(tester.no_coerce, 32767)

    def test_coerce_to_primitive_error(self):
        create_params = {**self.create_params, "no_coerce": "Value 32767"}

        with self.assertRaises(ValueError):
            self.MODEL_CLASS.objects.create(**create_params)

    def test_to_python_deferred_attribute(self):
        try:
            obj = self.MODEL_CLASS.objects.create(**self.create_params)
        except DatabaseError as err:
            print(str(err))
            if (
                IGNORE_ORA_01843
                and connection.vendor == "oracle"
                and "ORA-01843" in str(err)
            ):
                # this is an oracle bug - intermittent failure on
                # perfectly fine date format in SQL
                # TODO - remove when fixed
                pytest.skip("Oracle bug ORA-01843 encountered - skipping")
                return
            raise
        with self.assertNumQueries(1):
            obj2 = self.MODEL_CLASS.objects.only("id").get(pk=obj.pk)

        for field in [
            field.name for field in self.MODEL_CLASS._meta.fields if field.name != "id"
        ]:
            # each of these should result in a db query
            with self.assertNumQueries(1):
                self.assertEqual(getattr(obj, field), getattr(obj2, field))

            with self.assertNumQueries(2):
                self.assertEqual(
                    getattr(
                        self.MODEL_CLASS.objects.defer(field).get(pk=obj.pk), field
                    ),
                    getattr(obj, field),
                )

        # test that all coerced fields are coerced to the Enum type on
        # assignment - this also tests symmetric value assignment in the
        # derived class
        set_tester = self.MODEL_CLASS()
        for field, value in self.values_params.items():
            setattr(set_tester, field, getattr(value, "value", value))
            if self.MODEL_CLASS._meta.get_field(field).coerce:
                try:
                    self.assertIsInstance(
                        getattr(set_tester, field), self.enum_type(field)
                    )
                except AssertionError:
                    self.assertFalse(self.MODEL_CLASS._meta.get_field(field).strict)
                    self.assertIsInstance(
                        getattr(set_tester, field), self.enum_primitive(field)
                    )
            else:
                self.assertNotIsInstance(
                    getattr(set_tester, field), self.enum_type(field)
                )
                self.assertIsInstance(
                    getattr(set_tester, field), self.enum_primitive(field)
                )

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

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum="1").count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=1).count(), 1)
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum.ONE).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum(1)).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum["ONE"]).count(),
            1,
        )

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum="2").count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=2).count(), 1)
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum.TWO).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum(2)).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum["TWO"]).count(),
            1,
        )

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum="3").count(), 1)
        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_int_enum=3).count(), 1)
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum.THREE).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_int_enum=self.DJIntEnum(3)).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                dj_int_enum=self.DJIntEnum["THREE"]
            ).count(),
            1,
        )

    def test_text_choices(self):
        self.do_test_text_choices()

    def do_test_text_choices(self):
        self.MODEL_CLASS.objects.all().delete()
        self.MODEL_CLASS.objects.create(dj_text_enum=self.DJTextEnum.A)
        self.MODEL_CLASS.objects.create(dj_text_enum=self.DJTextEnum.B)
        self.MODEL_CLASS.objects.create(dj_text_enum=self.DJTextEnum.C)

        for obj in self.MODEL_CLASS.objects.all():
            self.assertIsInstance(obj.dj_text_enum, self.DJTextEnum)

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum="A").count(), 1)
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum.A).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum("A")).count(),
            1,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum["A"]).count(),
            1,
        )

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum="B").count(), 1)
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum.B).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum("B")).count(),
            1,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum["B"]).count(),
            1,
        )

        self.assertEqual(self.MODEL_CLASS.objects.filter(dj_text_enum="C").count(), 1)
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum.C).count(), 1
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum("C")).count(),
            1,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(dj_text_enum=self.DJTextEnum["C"]).count(),
            1,
        )

    @property
    def values_params(self):
        return {
            "small_pos_int": self.SmallPosIntEnum.VAL2,
            "small_int": self.SmallIntEnum.VALn1,
            "pos_int": self.PosIntEnum.VAL3,
            "int": self.IntEnum.VALn1,
            "big_pos_int": self.BigPosIntEnum.VAL3,
            "big_int": self.BigIntEnum.VAL2,
            "constant": self.Constants.GOLDEN_RATIO,
            "text": self.TextEnum.VALUE2,
            "extern": self.ExternEnum.TWO,
            "dj_int_enum": 3,
            "dj_text_enum": self.DJTextEnum.A,
            "non_strict_int": 75,
            "non_strict_text": "arbitrary",
            "no_coerce": self.SmallPosIntEnum.VAL2,
            "date_enum": self.DateEnum.EMMA,
            "datetime_enum": self.DateTimeEnum.ST_HELENS,
            "duration_enum": self.DurationEnum.DAY,
            "time_enum": self.TimeEnum.MORNING,
        }

    def do_test_values(self):
        """
        tests that queryset values returns Enumeration instances for enum
        fields
        """

        obj = self.MODEL_CLASS.objects.create(**self.values_params)

        values1 = self.MODEL_CLASS.objects.filter(pk=obj.pk).values().first()
        self.assertEqual(values1["small_pos_int"], self.SmallPosIntEnum.VAL2)
        self.assertEqual(values1["small_int"], self.SmallIntEnum.VALn1)
        self.assertEqual(values1["pos_int"], self.PosIntEnum.VAL3)
        self.assertEqual(values1["int"], self.IntEnum.VALn1)
        self.assertEqual(values1["big_pos_int"], self.BigPosIntEnum.VAL3)
        self.assertEqual(values1["big_int"], self.BigIntEnum.VAL2)
        self.assertEqual(values1["constant"], self.Constants.GOLDEN_RATIO)
        self.assertEqual(values1["text"], self.TextEnum.VALUE2)
        self.assertEqual(values1["extern"], self.ExternEnum.TWO)
        self.assertEqual(values1["dj_int_enum"], self.DJIntEnum.THREE)
        self.assertEqual(values1["dj_text_enum"], self.DJTextEnum.A)

        self.assertIsInstance(values1["small_pos_int"], self.SmallPosIntEnum)
        self.assertIsInstance(values1["small_int"], self.SmallIntEnum)
        self.assertIsInstance(values1["pos_int"], self.PosIntEnum)
        self.assertIsInstance(values1["int"], self.IntEnum)
        self.assertIsInstance(values1["big_pos_int"], self.BigPosIntEnum)
        self.assertIsInstance(values1["big_int"], self.BigIntEnum)
        self.assertIsInstance(values1["constant"], self.Constants)
        self.assertIsInstance(values1["text"], self.TextEnum)
        self.assertIsInstance(values1["dj_int_enum"], self.DJIntEnum)
        self.assertIsInstance(values1["dj_text_enum"], self.DJTextEnum)

        self.assertEqual(values1["non_strict_int"], 75)
        self.assertEqual(values1["non_strict_text"], "arbitrary")
        self.assertEqual(values1["no_coerce"], 2)

        self.assertNotIsInstance(values1["non_strict_int"], self.SmallPosIntEnum)
        self.assertNotIsInstance(values1["non_strict_text"], self.TextEnum)
        self.assertNotIsInstance(values1["no_coerce"], self.SmallPosIntEnum)

        obj.delete()

        obj = self.MODEL_CLASS.objects.create(
            non_strict_int=self.SmallPosIntEnum.VAL1,
            non_strict_text=self.TextEnum.VALUE3,
            no_coerce=self.SmallPosIntEnum.VAL3,
        )
        values2 = self.MODEL_CLASS.objects.filter(pk=obj.pk).values().first()
        self.assertEqual(values2["non_strict_int"], self.SmallPosIntEnum.VAL1)
        self.assertEqual(values2["non_strict_text"], self.TextEnum.VALUE3)
        self.assertEqual(values2["no_coerce"], self.SmallPosIntEnum.VAL3)
        self.assertIsInstance(values2["non_strict_int"], self.SmallPosIntEnum)
        self.assertIsInstance(values2["non_strict_text"], self.TextEnum)
        self.assertNotIsInstance(values2["no_coerce"], self.SmallPosIntEnum)

        self.assertEqual(values2["dj_int_enum"], 1)
        self.assertEqual(values2["dj_text_enum"], "A")

        return values1, values2

    def test_values(self):
        try:
            self.do_test_values()
        except DatabaseError as err:
            print(str(err))
            if (
                IGNORE_ORA_01843
                and connection.vendor == "oracle"
                and "ORA-01843" in str(err)
            ):
                # this is an oracle bug - intermittent failure on
                # perfectly fine date format in SQL
                # TODO - remove when fixed
                pytest.skip("Oracle bug ORA-01843 encountered - skipping")
                return
            raise

    def test_non_strict(self):
        """
        Test that non strict fields allow assignment and read of non-enum values.
        """
        values = {
            (self.SmallPosIntEnum.VAL1, self.TextEnum.VALUE1),
            (self.SmallPosIntEnum.VAL2, self.TextEnum.VALUE2),
            (self.SmallPosIntEnum.VAL3, self.TextEnum.VALUE3),
            (10, "arb"),
            (12, "arbitra"),
            (15, "A" * 12),
        }
        for int_val, txt_val in values:
            self.MODEL_CLASS.objects.create(
                non_strict_int=int_val, non_strict_text=txt_val
            )

        for obj in self.MODEL_CLASS.objects.filter(
            Q(non_strict_int__isnull=False) & Q(non_strict_text__isnull=False)
        ):
            self.assertTrue(obj.non_strict_int in [val[0] for val in values])
            self.assertTrue(obj.non_strict_text in [val[1] for val in values])

        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=self.SmallPosIntEnum.VAL1,
                non_strict_text=self.TextEnum.VALUE1,
            ).count(),
            1,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=self.SmallPosIntEnum.VAL2,
                non_strict_text=self.TextEnum.VALUE2,
            ).count(),
            1,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=self.SmallPosIntEnum.VAL3,
                non_strict_text=self.TextEnum.VALUE3,
            ).count(),
            1,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=10, non_strict_text="arb"
            ).count(),
            1,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=12, non_strict_text="arbitra"
            ).count(),
            1,
        )
        self.assertEqual(
            self.MODEL_CLASS.objects.filter(
                non_strict_int=15, non_strict_text="A" * 12
            ).count(),
            1,
        )

    def test_max_length_override(self):
        self.assertEqual(
            self.MODEL_CLASS._meta.get_field("non_strict_text").max_length, 12
        )
        # todo sqlite does not enforce the max_length of a VARCHAR, make this
        #   test specific to database backends that do
        # will raise in certain backends
        # obj = self.MODEL_CLASS.objects.create(
        #    non_strict_text='A'*13
        # )
        # print(len(obj.non_strict_text))

    def test_serialization(self):
        from pprint import pprint

        from django.db import connection
        from django.db.utils import DatabaseError

        with CaptureQueriesContext(connection) as ctx:
            # code that runs SQL queries
            try:
                tester = self.MODEL_CLASS.objects.create(**self.values_params)
            except DatabaseError as err:
                print(str(err))
                if (
                    IGNORE_ORA_01843
                    and connection.vendor == "oracle"
                    and "ORA-01843" in str(err)
                ):
                    # this is an oracle bug - intermittent failure on
                    # perfectly fine date format in SQL
                    # TODO - remove when fixed
                    pprint(ctx.captured_queries)
                    pytest.skip("Oracle bug ORA-01843 encountered - skipping")
                    return
                raise

        serialized = serializers.serialize("json", self.MODEL_CLASS.objects.all())

        tester.delete()

        for mdl in serializers.deserialize("json", serialized):
            mdl.save()
            tester = mdl.object

        for param, value in self.values_params.items():
            self.assertEqual(getattr(tester, param), value)

    def do_test_validate(self):
        tester = self.MODEL_CLASS.objects.create()
        self.assertRaises(
            ValidationError,
            tester._meta.get_field("small_pos_int").validate,
            666,
            tester,
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("small_int").validate, 666, tester
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("pos_int").validate, 666, tester
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("int").validate, 666, tester
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("big_pos_int").validate, 666, tester
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("big_int").validate, 666, tester
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("constant").validate, 66.6, tester
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("text").validate, "666", tester
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("extern").validate, 6, tester
        )

        # coerce=False still validates
        self.assertRaises(
            ValidationError, tester._meta.get_field("no_coerce").validate, 666, tester
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("no_coerce").validate, "a", tester
        )

        # non strict fields whose type can't be coerced to the enum's primitive will fail to validate
        self.assertRaises(
            ValidationError,
            tester._meta.get_field("non_strict_int").validate,
            "a",
            tester,
        )

        self.assertRaises(
            ValidationError,
            tester._meta.get_field("small_pos_int").validate,
            "anna",
            tester,
        )
        self.assertRaises(
            ValidationError,
            tester._meta.get_field("small_int").validate,
            "maria",
            tester,
        )
        self.assertRaises(
            ValidationError,
            tester._meta.get_field("pos_int").validate,
            "montes",
            tester,
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("int").validate, "3<", tester
        )
        self.assertRaises(
            ValidationError,
            tester._meta.get_field("big_pos_int").validate,
            "itwb",
            tester,
        )
        self.assertRaises(
            ValidationError,
            tester._meta.get_field("big_int").validate,
            "walwchh",
            tester,
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("constant").validate, "xx.x", tester
        )
        self.assertRaises(
            ValidationError, tester._meta.get_field("text").validate, "666", tester
        )

        self.assertRaises(
            ValidationError, tester._meta.get_field("small_int").validate, None, tester
        )

        self.assertTrue(
            tester._meta.get_field("small_pos_int").validate(0, tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("small_int").validate(-32768, tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("pos_int").validate(2147483647, tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("int").validate(-2147483648, tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("big_pos_int").validate(2147483648, tester) is None
        )
        self.assertTrue(tester._meta.get_field("big_int").validate(2, tester) is None)
        self.assertTrue(
            tester._meta.get_field("constant").validate(
                1.61803398874989484820458683436563811, tester
            )
            is None
        )
        self.assertTrue(tester._meta.get_field("text").validate("D", tester) is None)

        self.assertTrue(
            tester._meta.get_field("dj_int_enum").validate(1, tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("dj_text_enum").validate("A", tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("non_strict_int").validate(20, tester) is None
        )
        self.assertTrue(
            tester._meta.get_field("non_strict_text").validate("A" * 12, tester) is None
        )

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
            text="666",
            extern=6,
        )
        try:
            tester.full_clean()
            self.assertTrue(
                False, "full_clean should have thrown a ValidationError"
            )  # pragma: no cover
        except ValidationError as ve:
            self.assertTrue("small_pos_int" in ve.message_dict)
            self.assertTrue("small_int" in ve.message_dict)
            self.assertTrue("pos_int" in ve.message_dict)
            self.assertTrue("int" in ve.message_dict)
            self.assertTrue("big_pos_int" in ve.message_dict)
            self.assertTrue("big_int" in ve.message_dict)
            self.assertTrue("constant" in ve.message_dict)
            self.assertTrue("text" in ve.message_dict)
            self.assertTrue("extern" in ve.message_dict)

    @pytest.mark.skipif(
        find_spec("rest_framework") is not None, reason="rest_framework is installed"
    )
    def test_rest_framework_missing(self):
        with self.assertRaises(ImportError):
            from django_enum.drf import EnumField

    @pytest.mark.skipif(
        find_spec("django_filters") is not None, reason="django-filter is installed"
    )
    def test_django_filters_missing(self):
        with self.assertRaises(ImportError):
            from django_enum.filters import EnumFilter

    @pytest.mark.skipif(
        find_spec("enum_properties") is not None, reason="enum-properties is installed"
    )
    def test_enum_properties_missing(self):
        with self.assertRaises(ImportError):
            from django_enum.choices import TextChoices

        self.do_test_integer_choices()
        self.do_test_text_choices()
