from importlib.util import find_spec
import typing as t
from functools import reduce
from operator import or_
from enum import Flag
from tests.utils import FlagTypeMixin
from django.test import TestCase
from tests.djenum.models import FlagFilterTester
from django.urls import reverse
from bs4 import BeautifulSoup as Soup
from django.test import Client
from django.http import QueryDict
from django_enum.utils import decompose, get_set_values, get_set_bits


class TestFlagRequests(FlagTypeMixin, TestCase):
    MODEL_CLASS = FlagFilterTester
    NAMESPACE = "tests_djenum"

    objects = []
    values = {}

    maxDiff = None

    fields = ["small_flag", "flag", "flag_no_coerce", "big_flag"]

    def setUp(self):
        self.values = {val: {} for val in self.compared_attributes}
        self.objects = []
        self.MODEL_CLASS.objects.all().delete()
        self.objects.append(self.MODEL_CLASS.objects.create())
        self.objects[-1].refresh_from_db()

        self.objects.append(self.MODEL_CLASS.objects.create())
        self.objects.append(
            self.MODEL_CLASS.objects.create(
                small_flag=self.SmallPositiveFlagEnum.ONE,
                flag=self.PositiveFlagEnum.ONE,
                flag_no_coerce=self.PositiveFlagEnum.ONE.value,
                big_flag=self.BigPositiveFlagEnum.ONE,
            )
        )
        self.objects[-1].refresh_from_db()

        for _ in range(0, 2):
            self.objects.append(
                self.MODEL_CLASS.objects.create(
                    small_flag=self.SmallPositiveFlagEnum.ONE
                    | self.SmallPositiveFlagEnum.TWO,
                    flag=self.PositiveFlagEnum.ONE | self.PositiveFlagEnum.TWO,
                    flag_no_coerce=(
                        self.PositiveFlagEnum.ONE | self.PositiveFlagEnum.TWO
                    ).value,
                    big_flag=self.BigPositiveFlagEnum.ONE
                    | self.BigPositiveFlagEnum.TWO,
                )
            )
            self.objects[-1].refresh_from_db()

        for _ in range(0, 3):
            self.objects.append(
                self.MODEL_CLASS.objects.create(
                    small_flag=self.SmallPositiveFlagEnum.TWO
                    | self.SmallPositiveFlagEnum.FOUR
                    | self.SmallPositiveFlagEnum.FIVE,
                    flag=0,
                    flag_no_coerce=(
                        self.PositiveFlagEnum.FIVE | self.PositiveFlagEnum.FOUR
                    ).value,
                    big_flag=self.BigPositiveFlagEnum.ONE
                    | self.BigPositiveFlagEnum.TWO
                    | self.BigPositiveFlagEnum.THREE
                    | self.BigPositiveFlagEnum.FOUR,
                )
            )
            self.objects[-1].refresh_from_db()

        self.objects.append(
            # non-strict
            self.MODEL_CLASS.objects.create(
                big_flag=self.BigPositiveFlagEnum.ONE
                | self.BigPositiveFlagEnum.TWO
                | (1 << 32)
                | (1 << 23)
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
            "flag": self.PositiveFlagEnum.ONE | self.PositiveFlagEnum.TWO,
            "flag_no_coerce": self.PositiveFlagEnum(0),
            "big_flag": self.BigPositiveFlagEnum.ONE | (1 << 12) | (1 << 4),
        }

    @property
    def post_params_symmetric(self):
        return {**self.post_params}

    # if find_spec("rest_framework"):  # pragma: no cover

    #     def test_non_strict_drf_field(self):
    #         from rest_framework import fields

    #         from django_enum.drf import EnumField

    #         field = EnumField(self.SmallPosIntEnum, strict=False)
    #         self.assertEqual(field.to_internal_value("1"), 1)
    #         self.assertEqual(field.to_representation(1), 1)
    #         self.assertEqual(field.primitive_field.__class__, fields.IntegerField)

    #         field = EnumField(self.Constants, strict=False)
    #         self.assertEqual(field.to_internal_value("5.43"), 5.43)
    #         self.assertEqual(field.to_representation(5.43), 5.43)
    #         self.assertEqual(field.primitive_field.__class__, fields.FloatField)

    #         field = EnumField(self.TextEnum, strict=False)
    #         self.assertEqual(field.to_internal_value("random text"), "random text")
    #         self.assertEqual(field.to_representation("random text"), "random text")
    #         self.assertEqual(field.primitive_field.__class__, fields.CharField)

    #         field = EnumField(self.DateEnum, strict=False)
    #         self.assertEqual(
    #             field.to_internal_value("2017-12-05"), date(year=2017, day=5, month=12)
    #         )
    #         self.assertEqual(
    #             field.to_representation(date(year=2017, day=5, month=12)),
    #             date(year=2017, day=5, month=12),
    #         )
    #         self.assertEqual(field.primitive_field.__class__, fields.DateField)

    #         field = EnumField(self.DateTimeEnum, strict=False)
    #         self.assertEqual(
    #             field.to_internal_value("2017-12-05T01:02:30Z"),
    #             datetime(year=2017, day=5, month=12, hour=1, minute=2, second=30),
    #         )
    #         self.assertEqual(
    #             field.to_representation(
    #                 datetime(year=2017, day=5, month=12, hour=1, minute=2, second=30)
    #             ),
    #             datetime(year=2017, day=5, month=12, hour=1, minute=2, second=30),
    #         )
    #         self.assertEqual(field.primitive_field.__class__, fields.DateTimeField)

    #         field = EnumField(self.DurationEnum, strict=False)
    #         self.assertEqual(
    #             field.to_internal_value("P5DT01H00M01.312500S"),
    #             timedelta(days=5, hours=1, seconds=1.3125),
    #         )
    #         self.assertEqual(
    #             field.to_representation(timedelta(days=5, hours=1, seconds=1.3125)),
    #             timedelta(days=5, hours=1, seconds=1.3125),
    #         )
    #         self.assertEqual(field.primitive_field.__class__, fields.DurationField)

    #         field = EnumField(self.TimeEnum, strict=False)
    #         self.assertEqual(
    #             field.to_internal_value("01:02:30"), time(hour=1, minute=2, second=30)
    #         )
    #         self.assertEqual(
    #             field.to_representation(time(hour=1, minute=2, second=30)),
    #             time(hour=1, minute=2, second=30),
    #         )
    #         self.assertEqual(field.primitive_field.__class__, fields.TimeField)

    #         field = EnumField(self.DecimalEnum, strict=False)
    #         self.assertEqual(field.to_internal_value("1.67"), Decimal("1.67"))
    #         self.assertEqual(field.to_representation(Decimal("1.67")), Decimal("1.67"))
    #         self.assertEqual(field.primitive_field.__class__, fields.DecimalField)

    #         from enum import Enum

    #         class UnsupportedPrimitiveEnum(Enum):
    #             VAL1 = (1,)
    #             VAL2 = (1, 2)
    #             VAL3 = (1, 2, 3)

    #         field = EnumField(
    #             UnsupportedPrimitiveEnum,
    #             strict=False,
    #             choices=[
    #                 (UnsupportedPrimitiveEnum.VAL1, "VAL1"),
    #                 (UnsupportedPrimitiveEnum.VAL2, "VAL2"),
    #                 (UnsupportedPrimitiveEnum.VAL3, "VAL3"),
    #             ],
    #         )
    #         self.assertEqual(field.to_internal_value((1, 2, 4)), (1, 2, 4))
    #         self.assertEqual(field.to_representation((1, 2, 4)), (1, 2, 4))
    #         self.assertIsNone(field.primitive_field)

    #     def test_drf_serializer(self):
    #         from rest_framework import serializers

    #         from django_enum.drf import EnumField

    #         class TestSerializer(serializers.ModelSerializer):
    #             small_pos_int = EnumField(self.SmallPosIntEnum)
    #             small_int = EnumField(self.SmallIntEnum)
    #             pos_int = EnumField(self.PosIntEnum)
    #             int = EnumField(self.IntEnum)
    #             big_pos_int = EnumField(self.BigPosIntEnum)
    #             big_int = EnumField(self.BigIntEnum)
    #             constant = EnumField(self.Constants)
    #             date_enum = EnumField(self.DateEnum)
    #             datetime_enum = EnumField(self.DateTimeEnum, strict=False)
    #             duration_enum = EnumField(self.DurationEnum)
    #             time_enum = EnumField(self.TimeEnum)
    #             decimal_enum = EnumField(self.DecimalEnum)
    #             text = EnumField(self.TextEnum)
    #             extern = EnumField(self.ExternEnum)
    #             dj_int_enum = EnumField(self.DJIntEnum)
    #             dj_text_enum = EnumField(self.DJTextEnum)
    #             non_strict_int = EnumField(self.SmallPosIntEnum, strict=False)
    #             non_strict_text = EnumField(
    #                 self.TextEnum, strict=False, allow_blank=True
    #             )
    #             no_coerce = EnumField(self.SmallPosIntEnum)

    #             class Meta:
    #                 model = self.MODEL_CLASS
    #                 fields = "__all__"

    #         ser = TestSerializer(data=self.post_params)
    #         self.assertTrue(ser.is_valid())
    #         inst = ser.save()
    #         for param, value in self.post_params.items():
    #             self.assertEqual(value, getattr(inst, param))

    #         ser_bad = TestSerializer(
    #             data={
    #                 **self.post_params,
    #                 "small_pos_int": -1,
    #                 "constant": 3.14,
    #                 "text": "wrong",
    #                 "extern": 0,
    #                 "pos_int": -50,
    #                 "date_enum": date(year=2017, day=5, month=12),
    #                 "decimal_enum": Decimal("1.89"),
    #             }
    #         )

    #         self.assertFalse(ser_bad.is_valid())
    #         self.assertTrue("small_pos_int" in ser_bad.errors)
    #         self.assertTrue("constant" in ser_bad.errors)
    #         self.assertTrue("text" in ser_bad.errors)
    #         self.assertTrue("extern" in ser_bad.errors)
    #         self.assertTrue("pos_int" in ser_bad.errors)
    #         self.assertTrue("date_enum" in ser_bad.errors)
    #         self.assertTrue("decimal_enum" in ser_bad.errors)

    #     def test_drf_read(self):
    #         c = Client()
    #         response = c.get(reverse(f"{self.NAMESPACE}:enumtester-list"))
    #         read_objects = response.json()
    #         self.assertEqual(len(read_objects), len(self.objects))

    #         for idx, obj in enumerate(response.json()):
    #             # should be same order
    #             self.assertEqual(obj["id"], self.objects[idx].id)
    #             for field in self.fields:
    #                 self.assertEqual(obj[field], getattr(self.objects[idx], field))
    #                 if obj[field] is not None:
    #                     self.assertIsInstance(
    #                         try_convert(
    #                             self.enum_primitive(field),
    #                             obj[field],
    #                             raise_on_error=False,
    #                         ),
    #                         self.enum_primitive(field),
    #                     )

    #     def test_drf_update(self):
    #         c = Client()
    #         params = self.post_params_symmetric
    #         response = c.put(
    #             reverse(
    #                 f"{self.NAMESPACE}:enumtester-detail",
    #                 kwargs={"pk": self.objects[0].id},
    #             ),
    #             params,
    #             follow=True,
    #             content_type="application/json",
    #         )
    #         self.assertEqual(response.status_code, 200)
    #         fetched = c.get(
    #             reverse(
    #                 f"{self.NAMESPACE}:enumtester-detail",
    #                 kwargs={"pk": self.objects[0].id},
    #             ),
    #             follow=True,
    #         ).json()

    #         obj = self.MODEL_CLASS.objects.get(pk=self.objects[0].id)

    #         self.assertEqual(fetched["id"], obj.id)
    #         for field in self.fields:
    #             self.assertEqual(
    #                 try_convert(
    #                     self.enum_primitive(field), fetched[field], raise_on_error=False
    #                 ),
    #                 getattr(obj, field),
    #             )
    #             if self.MODEL_CLASS._meta.get_field(field).coerce:
    #                 self.assertEqual(params[field], getattr(obj, field))

    #     def test_drf_post(self):
    #         c = Client()
    #         params = {**self.post_params_symmetric, "non_strict_text": "", "text": None}
    #         response = c.post(
    #             reverse(f"{self.NAMESPACE}:enumtester-list"),
    #             params,
    #             follow=True,
    #             content_type="application/json",
    #         )
    #         self.assertEqual(response.status_code, 201)
    #         created = response.json()

    #         obj = self.MODEL_CLASS.objects.last()

    #         self.assertEqual(created["id"], obj.id)
    #         for field in self.fields:
    #             self.assertEqual(
    #                 getattr(obj, field),
    #                 try_convert(
    #                     self.enum_primitive(field), created[field], raise_on_error=False
    #                 ),
    #             )
    #             if self.MODEL_CLASS._meta.get_field(field).coerce:
    #                 self.assertEqual(getattr(obj, field), params[field])

    def test_add(self):
        """
        Test that add forms work and that EnumField type allows creations
        from symmetric values
        """
        c = Client()

        # test normal choice field and our EnumFlagField
        form_url = "flag-add"
        params = self.post_params_symmetric
        response = c.post(
            reverse(f"{self.NAMESPACE}:{form_url}"),
            {f: getattr(v, "value", v) for f, v in params.items()},
            follow=True,
        )
        soup = Soup(response.content, features="html.parser")
        added_resp = soup.find_all("div", class_="enum")[-1]
        added = self.MODEL_CLASS.objects.last()

        for param, value in params.items():
            field = self.MODEL_CLASS._meta.get_field(param)
            value = self.get_enum_val(field.enum, value)
            form_val = self.get_enum_val(
                field.enum,
                added_resp.find(class_=param).find("span", class_="value").text,
            )
            if form_val is None and not (field.null and field.blank):
                form_val = field.enum(0)
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
        form_url = "flag-update"
        params = self.post_params_symmetric
        updated = self.MODEL_CLASS.objects.create()
        response = c.post(
            reverse(f"{self.NAMESPACE}:{form_url}", kwargs={"pk": updated.pk}),
            data={f: getattr(v, "value", v) for f, v in params.items()},
            follow=True,
        )
        self.assertLess(response.status_code, 300)
        updated.refresh_from_db()
        soup = Soup(response.content, features="html.parser")
        self.verify_form(updated, soup)

        for param, value in params.items():
            if (
                not self.MODEL_CLASS._meta.get_field(param).coerce
                and self.MODEL_CLASS._meta.get_field(param).strict
            ):
                value = self.enum_type(param)(value)
            self.assertEqual(getattr(updated, param), value)
        updated.delete()

    def test_delete(self):
        c = Client()
        form_url = "flag-delete"
        deleted = self.MODEL_CLASS.objects.create()
        c.delete(reverse(f"{self.NAMESPACE}:{form_url}", kwargs={"pk": deleted.pk}))
        self.assertRaises(
            self.MODEL_CLASS.DoesNotExist, self.MODEL_CLASS.objects.get, pk=deleted.pk
        )

    def get_enum_val(self, enum, value):
        if value == "":
            return None
        return enum(int(value))

    def test_add_form(self):
        c = Client()
        # test normal choice field and our EnumChoiceField
        form_url = "flag-add"
        response = c.get(reverse(f"{self.NAMESPACE}:{form_url}"))
        soup = Soup(response.content, features="html.parser")
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
            field_value = getattr(obj, field.name)
            values_at_bit = list(
                zip(
                    get_set_values(field_value),
                    get_set_bits(field_value),
                )
            )
            expected = {}
            for val, label in field.choices:
                expected[
                    self.get_enum_val(field.enum, val) if field.coerce else val
                ] = label

            if not field.strict:
                choices = {val for val, _ in field.choices}
                for val, bit in values_at_bit:
                    if val not in choices:
                        expected[val] = bit

            selected = []
            num_options = 0
            field_element = soup.find("select", id=f"id_{field.name}")
            if field_element is None:
                import ipdb

                ipdb.set_trace()
            for option in field_element.find_all("option"):
                num_options += 1
                raw = int(option["value"])
                try:
                    value = self.get_enum_val(field.enum, raw)
                except ValueError:
                    if raw not in expected:
                        raise
                    value = raw
                self.assertTrue(value in expected)
                self.assertEqual(str(expected[value]), option.text)

                if option.has_attr("selected"):
                    selected.append(value)
            if not selected:
                if field.null and field.default is None:
                    self.assertIsNone(field_value)
                else:
                    self.assertEqual(field_value, field.enum(0))
            else:
                self.assertEqual(field_value, reduce(or_, selected))

            self.assertEqual(len(expected), num_options)
            if field.strict:
                self.assertEqual(len(expected), 5)
            else:
                self.assertGreaterEqual(len(expected), 5)

    def test_update_form(self):
        client = Client()
        # test normal choice field and our EnumChoiceField
        form_url = "flag-update"
        for obj in self.objects:
            response = client.get(
                reverse(f"{self.NAMESPACE}:{form_url}", kwargs={"pk": obj.pk})
            )
            soup = Soup(response.content, features="html.parser")
            self.verify_form(obj, soup)

    def test_non_strict_select(self):
        client = Client()
        obj = self.MODEL_CLASS.objects.create(big_flag=(1 << 22) | (1 << 32))
        form_url = "flag-update"
        response = client.get(
            reverse(f"{self.NAMESPACE}:{form_url}", kwargs={"pk": obj.pk})
        )
        soup = Soup(response.content, features="html.parser")
        self.verify_form(obj, soup)
        selected = 0
        for option in soup.find("select", id=f"id_big_flag").find_all("option"):
            if option.has_attr("selected"):
                selected |= int(option["value"])
        self.assertEqual(selected, (1 << 22) | (1 << 32))

    @property
    def field_filter_properties(self):
        return {
            "small_flag": ["value", "name"],
            "flag": ["value", "name"],
            "flag_no_coerce": ["value", "name"],
            "big_flag": ["value", "name"],
        }

    @property
    def compared_attributes(self):
        return ["small_flag", "flag", "flag_no_coerce", "big_flag"]

    def list_to_objects(self, resp_content):
        objects = {}
        for obj_div in resp_content.find("body").find_all(f"div", class_="enum"):
            objects[int(obj_div["data-obj-id"])] = {
                attr: self.get_enum_val(
                    self.MODEL_CLASS._meta.get_field(attr).enum,
                    obj_div.find(f"p", {"class": attr})
                    .find("span", class_="value")
                    .text,
                )
                for attr in self.compared_attributes
            }
        return objects

    if find_spec("django_filters"):  # pragma: no cover

        def test_filter_misc_behavior(self):
            from django_enum.filters import EnumFlagFilter

            filter = EnumFlagFilter(enum=self.SmallPositiveFlagEnum)
            qry = FlagFilterTester.objects
            self.assertTrue(filter.is_noop(qry, None))
            self.assertTrue(filter.is_noop(qry, ""))
            self.assertFalse(
                filter.is_noop(
                    qry,
                    [
                        self.SmallPositiveFlagEnum.ONE,
                        self.SmallPositiveFlagEnum.TWO,
                        self.SmallPositiveFlagEnum.THREE,
                        self.SmallPositiveFlagEnum.FOUR,
                        self.SmallPositiveFlagEnum.FIVE,
                    ],
                )
            )
            self.assertFalse(
                filter.is_noop(
                    qry,
                    self.SmallPositiveFlagEnum.ONE
                    | self.SmallPositiveFlagEnum.TWO
                    | self.SmallPositiveFlagEnum.THREE
                    | self.SmallPositiveFlagEnum.FOUR
                    | self.SmallPositiveFlagEnum.FIVE,
                )
            )
            self.assertIs(qry, filter.filter(qry, None))
            self.assertIs(qry, filter.filter(qry, ""))

        def test_django_filter_flags(self):
            self.do_test_django_filter(reverse(f"{self.NAMESPACE}:flag-filter"))

        def test_django_filter_flags_exclude(self):
            self.do_test_django_filter(
                reverse(f"{self.NAMESPACE}:flag-filter-exclude"), exclude=True
            )

        def test_django_filter_flags_conjoined(self):
            self.do_test_django_filter(
                reverse(f"{self.NAMESPACE}:flag-filter-conjoined"), conjoined=True
            )

        def test_django_filter_flags_conjoined_exclude(self):
            self.do_test_django_filter(
                reverse(f"{self.NAMESPACE}:flag-filter-conjoined-exclude"),
                exclude=True,
                conjoined=True,
            )

        def do_test_django_filter(self, url, conjoined=False, exclude=False):
            """
            Exhaustively test query parameter permutations based on data
            created in setUp
            """
            filter = (
                self.MODEL_CLASS.objects.exclude
                if exclude
                else self.MODEL_CLASS.objects.filter
            )
            client = Client()
            for attr, val_map in self.values.items():
                field = self.MODEL_CLASS._meta.get_field(attr)
                tests: t.List[t.Tuple[t.Any, t.List[int]]] = []
                for val, objs in val_map.items():
                    if val in {None, ""}:
                        # todo how to query None or empty?
                        # set = null
                        continue
                    expected = objs.copy()
                    if val:
                        for v, o in val_map.items():
                            if v is None:
                                continue
                            if conjoined:
                                if (val & v) == val:
                                    expected.extend(o)
                            elif val & v:
                                expected.extend(o)

                    tests.append((val, set(expected)))

                for tid, (val, exp) in enumerate(tests):
                    for prop in self.field_filter_properties[attr]:
                        qry = QueryDict(mutable=True)

                        # decompose into the list of query items
                        flags = []
                        to_find = []
                        if isinstance(val, Flag):
                            flags = decompose(val)
                            to_find = [getattr(f, prop) for f in flags]
                        if not field.strict or not field.coerce:
                            to_find += [
                                str(v)
                                for v in get_set_values(val)
                                if v not in {f.value for f in flags}
                            ]
                        if not to_find:
                            to_find = [0]
                        qry.setlist(attr, to_find)
                        objects = {
                            obj.pk: {
                                attr: getattr(obj, attr)
                                for attr in self.compared_attributes
                            }
                            for obj in filter(id__in=exp).distinct()
                        }
                        if exclude:
                            self.assertEqual(
                                len(set(objects)),
                                self.MODEL_CLASS.objects.count() - len(set(exp)),
                            )
                        else:
                            self.assertEqual(len(objects), len(exp))
                        response = client.get(f"{url}?{qry.urlencode()}")
                        resp_objects = self.list_to_objects(
                            Soup(response.content, features="html.parser")
                        )
                        self.assertEqual(
                            objects,
                            resp_objects,
                            f"{objects.keys()} != {resp_objects.keys()}: {tests[tid]} {to_find=} {qry=}",
                        )

                        print(f"{attr=} | {qry=} | {len(objects)}")
