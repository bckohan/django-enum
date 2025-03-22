import typing as t
import os
from enum import Enum, Flag
from tests.utils import EnumTypeMixin
from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django_enum import EnumField
from tests.djenum.models import (
    AdminDisplayBug35,
    EnumTester,
    NullBlankFormTester,
    NullableBlankFormTester,
    Bug53Tester,
    NullableStrFormTester,
)
from tests.djenum.enums import (
    ExternEnum,
    NullableExternEnum,
    StrTestEnum,
    NullableStrEnum,
)
from playwright.sync_api import sync_playwright, expect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Model
from django.db.models.fields import NOT_PROVIDED
from django_enum.utils import decompose
from django.db import connection


class TestAdmin(EnumTypeMixin, LiveServerTestCase):
    BUG35_CLASS = AdminDisplayBug35

    def test_admin_list_display_bug35(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_superuser(
            username="admin",
            email="admin@django-enum.com",
            password="admin_password",
        )
        self.client.login(username="admin", password="admin_password")

        obj = self.BUG35_CLASS.objects.create()

        resp = self.client.get(
            reverse(
                f"admin:{self.BUG35_CLASS._meta.label_lower.replace('.', '_')}_changelist"
            )
        )
        self.assertContains(resp, '<td class="field-int_enum">Value 2</td>')
        change_link = reverse(
            f"admin:{self.BUG35_CLASS._meta.label_lower.replace('.', '_')}_change",
            args=[obj.id],
        )
        self.assertContains(resp, f'<a href="{change_link}">Value1</a>')

    def test_admin_change_display_bug35(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_superuser(
            username="admin",
            email="admin@django-enum.com",
            password="admin_password",
        )
        self.client.login(username="admin", password="admin_password")

        obj = self.BUG35_CLASS.objects.create()
        resp = self.client.get(
            reverse(
                f"admin:{self.BUG35_CLASS._meta.label_lower.replace('.', '_')}_change",
                args=[obj.id],
            )
        )
        self.assertContains(resp, '<div class="readonly">Value1</div>')
        self.assertContains(resp, '<div class="readonly">Value 2</div>')


class _GenericAdminFormTest(StaticLiveServerTestCase):
    MODEL_CLASS: Model

    HEADLESS = True

    __test__ = False

    def enum(self, field):
        return self.MODEL_CLASS._meta.get_field(field).enum

    @property
    def changes(self) -> t.List[t.Dict[str, Enum]]:
        # must implement
        return [{}]

    @property
    def add_url(self):
        path = reverse(
            f"admin:{self.MODEL_CLASS._meta.label_lower.replace('.', '_')}_add"
        )
        return f"{self.live_server_url}{path}"

    def change_url(self, id):
        path = reverse(
            f"admin:{self.MODEL_CLASS._meta.label_lower.replace('.', '_')}_change",
            args=[id],
        )
        return f"{self.live_server_url}{path}"

    @property
    def list_url(self):
        path = reverse(
            f"admin:{self.MODEL_CLASS._meta.label_lower.replace('.', '_')}_changelist"
        )
        return f"{self.live_server_url}{path}"

    def get_object_ids(self):
        self.page.goto(self.list_url)
        return self.page.eval_on_selector_all(
            "input[name='_selected_action']", "elements => elements.map(e => e.value)"
        )

    @classmethod
    def setUpClass(cls):
        """Set up the test class with a live server and Playwright instance."""
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "1"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=cls.HEADLESS)
        cls.page = cls.browser.new_page()

    @classmethod
    def tearDownClass(cls):
        """Clean up Playwright instance after tests."""
        cls.page.close()
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()
        del os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"]

    def setUp(self):
        """Create an admin user before running tests."""
        self.admin_username = "admin"
        self.admin_password = "password"

        get_user_model().objects.create_superuser(
            username=self.admin_username, password=self.admin_password
        )

        # Log in to the Django admin
        self.page.goto(f"{self.live_server_url}/admin/login/")
        self.page.fill("input[name='username']", self.admin_username)
        self.page.fill("input[name='password']", self.admin_password)
        self.page.click("input[type='submit']")

        # Ensure login is successful
        expect(self.page).to_have_url(f"{self.live_server_url}/admin/")

    def set_form_value(
        self, field_name: str, value: t.Optional[t.Union[Enum, str]], flag=False
    ):
        try:
            if value is None and None in self.enum(field_name):
                value = self.enum(field_name)(value)
            # should override this if needed
            if getattr(value, "value", value) is None and not flag:
                self.page.select_option(f"select[name='{field_name}']", "")
            elif flag:
                self.page.select_option(
                    f"select[name='{field_name}']",
                    [str(flag.value) for flag in decompose(value)],
                )
            else:
                self.page.select_option(
                    f"select[name='{field_name}']", str(getattr(value, "value", value))
                )
        except Exception:
            self.page.pause()

    def verify_changes(self, obj: Model, expected: t.Dict[str, t.Any]):
        count = 0
        for field in obj._meta.get_fields():
            if field.name == "id":
                continue
            if field.name not in expected:
                continue
            if not isinstance(field, EnumField):
                continue
            count += 1
            obj_val = getattr(obj, field.name)
            exp = expected[field.name]
            if not field.coerce:
                exp = getattr(exp, "value", exp)
            if exp is None or (isinstance(exp, str) and not exp):
                if isinstance(obj_val, Enum):
                    self.assertIsNone(
                        obj_val.value, f"{obj._meta.model_name}.{field.name}"
                    )
                elif isinstance(obj_val, str):
                    self.assertEqual(
                        obj_val, exp, f"{obj._meta.model_name}.{field.name}"
                    )
                else:
                    try:
                        self.assertIsNone(
                            obj_val, f"{obj._meta.model_name}.{field.name}"
                        )
                    except AssertionError:
                        if connection.vendor == "oracle" and issubclass(
                            field.enum, Flag
                        ):
                            # TODO - why is oracle returning 0 instead of None?
                            self.assertEqual(obj_val, field.enum(0))
                        else:
                            raise
            else:
                self.assertEqual(obj_val, exp, f"{obj._meta.model_name}.{field.name}")

        # sanity check
        self.assertEqual(count, len(expected))

    def test_admin_form_add_change_delete(self):
        """Tests add, change, and delete operations in Django Admin."""

        obj_ids = set(self.get_object_ids())

        self.page.goto(self.add_url)

        for field, value in self.changes[0].items():
            self.set_form_value(
                field,
                value,
                flag=issubclass(self.MODEL_CLASS._meta.get_field(field).enum, Flag),
            )

        # create with all default fields
        self.page.click("input[name='_save']")

        # verify the add
        added_obj = self.MODEL_CLASS.objects.get(
            id=list(set(self.get_object_ids()) - obj_ids)[0]
        )

        defaults = {}

        for field in added_obj._meta.get_fields():
            if field.name == "id" or not isinstance(field, EnumField):
                continue
            enum = getattr(field, "enum", None)
            expected = field.default
            if field.default is NOT_PROVIDED:
                expected = None
                if enum and issubclass(enum, Flag) and not field.null:
                    expected = enum(0)
            defaults[field.name] = expected

        self.verify_changes(added_obj, {**defaults, **self.changes[0]})

        # test change forms
        for changes in self.changes[1:]:
            # go to the change page
            self.page.goto(self.change_url(added_obj.id))

            # make form selections
            for field, value in changes.items():
                self.set_form_value(
                    field,
                    value,
                    flag=issubclass(self.MODEL_CLASS._meta.get_field(field).enum, Flag),
                )

            # save
            self.page.click("input[name='_save']")

            added_obj.refresh_from_db()
            self.verify_changes(added_obj, changes)

        # delete the object
        self.page.goto(self.change_url(added_obj.id))
        self.page.click("a.deletelink")
        self.page.click("input[type='submit']")

        # verify deletion
        self.assertFalse(self.MODEL_CLASS.objects.filter(pk=added_obj.pk).exists())


class TestEnumTesterAdminForm(EnumTypeMixin, _GenericAdminFormTest):
    MODEL_CLASS = EnumTester
    __test__ = True

    @property
    def changes(self) -> t.Dict[str, Enum]:
        return [
            {},
            {
                "small_pos_int": self.SmallPosIntEnum.VAL2,
                "small_int": self.SmallIntEnum.VAL0,
                "pos_int": self.PosIntEnum.VAL1,
                "int": self.IntEnum.VALn1,
                "big_pos_int": self.BigPosIntEnum.VAL2,
                "big_int": self.BigIntEnum.VAL2,
                "constant": self.Constants.GOLDEN_RATIO,
                "text": self.TextEnum.VALUE2,
                "extern": self.ExternEnum.TWO,
                "date_enum": self.DateEnum.EMMA,
                "datetime_enum": self.DateTimeEnum.ST_HELENS,
                "duration_enum": self.DurationEnum.DAY,
                "time_enum": self.TimeEnum.MORNING,
                "decimal_enum": self.DecimalEnum.ONE,
                "dj_int_enum": self.DJIntEnum.TWO,
                "dj_text_enum": self.DJTextEnum.C,
                "non_strict_int": self.SmallPosIntEnum.VAL1,
                "non_strict_text": self.TextEnum.VALUE3,
                "no_coerce": self.SmallPosIntEnum.VAL3,
            },
        ]


class TestNullBlankAdminBehavior(_GenericAdminFormTest):
    MODEL_CLASS = NullBlankFormTester
    __test__ = True

    @property
    def changes(self) -> t.Dict[str, Enum]:
        return [
            {"required": ExternEnum.THREE, "blank": ExternEnum.TWO},
            {
                "required": ExternEnum.ONE,
                "required_default": ExternEnum.THREE,
                "blank": ExternEnum.ONE,
                "blank_nullable": None,
                "blank_nullable_default": None,
            },
            {
                "required": ExternEnum.ONE,
                "required_default": ExternEnum.THREE,
                "blank": ExternEnum.ONE,
                "blank_nullable": ExternEnum.ONE,
                "blank_nullable_default": ExternEnum.TWO,
            },
            {
                "required": ExternEnum.ONE,
                "required_default": ExternEnum.THREE,
                "blank": ExternEnum.ONE,
                "blank_nullable": "",
                "blank_nullable_default": "",
            },
        ]


class TestNullableBlankAdminBehavior(_GenericAdminFormTest):
    MODEL_CLASS = NullableBlankFormTester
    __test__ = True
    HEADLESS = True

    @property
    def changes(self) -> t.Dict[str, Enum]:
        return [
            {"required": NullableExternEnum.THREE, "blank": NullableExternEnum.TWO},
            {
                "required": NullableExternEnum.ONE,
                "required_default": NullableExternEnum.THREE,
                "blank": NullableExternEnum.ONE,
                "blank_nullable": None,
                "blank_nullable_default": None,
            },
            {
                "required": NullableExternEnum.ONE,
                "required_default": NullableExternEnum.THREE,
                "blank": NullableExternEnum.ONE,
                "blank_nullable": NullableExternEnum.ONE,
                "blank_nullable_default": NullableExternEnum.TWO,
            },
            {
                "required": NullableExternEnum.ONE,
                "required_default": NullableExternEnum.THREE,
                "blank": NullableExternEnum.ONE,
                "blank_nullable": "",
                "blank_nullable_default": "",
            },
        ]


class TestNullableStrAdminBehavior(_GenericAdminFormTest):
    MODEL_CLASS = NullableStrFormTester
    __test__ = True
    HEADLESS = True

    @property
    def changes(self) -> t.Dict[str, Enum]:
        return [
            {"required": NullableStrEnum.STR1, "blank": NullableStrEnum.STR2},
            {
                "required": NullableStrEnum.STR2,
                "required_default": NullableStrEnum.STR1,
                "blank": NullableStrEnum.STR2,
                "blank_nullable": None,
                "blank_nullable_default": None,
            },
            {
                "required": NullableStrEnum.STR1,
                "required_default": NullableStrEnum.STR2,
                "blank": NullableStrEnum.STR2,
                "blank_nullable": NullableStrEnum.STR1,
                "blank_nullable_default": NullableStrEnum.NONE,
            },
            {
                "required": NullableStrEnum.STR2,
                "required_default": NullableStrEnum.STR2,
                "blank": NullableStrEnum.STR1,
                "blank_nullable": "",
                "blank_nullable_default": "",
            },
        ]


class TestBug53AdminBehavior(_GenericAdminFormTest):
    MODEL_CLASS = Bug53Tester
    __test__ = True

    @property
    def changes(self) -> t.Dict[str, Enum]:
        return [
            {
                "char_blank_null_false": StrTestEnum.V2,
                "int_blank_null_false": ExternEnum.TWO,
            },
        ]

    def test_500_error(self):
        # when null=False and blank=True on an enum field that has an enum that
        # does not accept the blank value "" a value error will be allowed to propagate out
        # of the form.save(). This is expected and on the user of the library to address. It
        # happens because "" is fine given the form logic definiton but is not given the database
        # requirements. Nothing to do about it.

        self.page.goto(self.add_url)

        # make form selections
        for field, value in {"char_blank_null_false": StrTestEnum.V2}.items():
            self.set_form_value(field, value)

        # save
        with self.page.expect_response(lambda response: response.status == 500):
            self.page.click("input[name='_save']")
