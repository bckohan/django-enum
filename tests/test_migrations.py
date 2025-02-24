import os
from tests.test_constraints import DISABLE_CONSTRAINT_TESTS
import pytest
from django import VERSION as django_version
from django.test import TestCase
from django.core.management import call_command
from django.db import migrations
from django.db.models import Q
from pathlib import Path
from importlib import import_module
from django_test_migrations.constants import MIGRATION_TEST_MARKER
from django_test_migrations.contrib.unittest_case import MigratorTestCase


pytest.importorskip("enum_properties")
if DISABLE_CONSTRAINT_TESTS:
    pytest.mark.skip(reason="Requires constraint support and enum_properties")


condition = "condition" if django_version[0:2] >= (5, 1) else "check"


def import_migration(migration):
    return import_module(
        str(migration.relative_to(Path(__file__).parent.parent))
        .replace("/", ".")
        .replace("\\", ".")
        .replace(".py", "")
    ).Migration


def set_models(version):
    import warnings
    from importlib import reload
    from shutil import copyfile

    from django.conf import settings

    from .edit_tests import models

    copyfile(
        settings.TEST_EDIT_DIR / f"_{version}.py",
        settings.TEST_MIGRATION_DIR.parent / "models.py",
    )

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        reload(models)


class ResetModelsMixin:
    @classmethod
    def tearDownClass(cls):
        from django.conf import settings

        with open(settings.TEST_MIGRATION_DIR.parent / "models.py", "w") as models_file:
            models_file.write("")

        super().tearDownClass()


class TestMigrations(ResetModelsMixin, TestCase):
    """Run through migrations"""

    @classmethod
    def setUpClass(cls):
        import glob

        from django.conf import settings

        for migration in glob.glob(f"{settings.TEST_MIGRATION_DIR}/00*py"):
            os.remove(migration)

        super().setUpClass()

    def test_makemigrate_01(self):
        from django.conf import settings

        set_models(1)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0001_initial.py")
        )

        call_command("makemigrations")

        self.assertTrue(os.path.isfile(settings.TEST_MIGRATION_DIR / "0001_initial.py"))

        migration = import_migration(settings.TEST_MIGRATION_DIR / "0001_initial.py")
        if django_version >= (5, 1):
            self.assertIsInstance(migration.operations[0], migrations.CreateModel)
            self.assertEqual(len(migration.operations[0].options["constraints"]), 2)
            self.assertEqual(
                migration.operations[0].options["constraints"][0].name,
                "tests_edit_tests_MigrationTester_int_enum_IntEnum",
            )
            self.assertEqual(
                migration.operations[0].options["constraints"][0].condition,
                Q(int_enum__in=[0, 1, 2]),
            )
            self.assertEqual(
                migration.operations[0].options["constraints"][1].name,
                "tests_edit_tests_MigrationTester_color_Color",
            )
            self.assertEqual(
                migration.operations[0].options["constraints"][1].condition,
                Q(color__in=["R", "G", "B", "K"]),
            )
        else:
            self.assertIsInstance(migration.operations[1], migrations.AddConstraint)
            self.assertEqual(
                migration.operations[1].constraint.check, Q(int_enum__in=[0, 1, 2])
            )
            self.assertEqual(
                migration.operations[1].constraint.name,
                "tests_edit_tests_MigrationTester_int_enum_IntEnum",
            )
            self.assertIsInstance(migration.operations[2], migrations.AddConstraint)
            self.assertEqual(
                migration.operations[2].constraint.check,
                Q(color__in=["R", "G", "B", "K"]),
            )
            self.assertEqual(
                migration.operations[2].constraint.name,
                "tests_edit_tests_MigrationTester_color_Color",
            )

    def test_makemigrate_02(self):
        import shutil

        from django.conf import settings

        set_models(2)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0002_alter_values.py")
        )

        call_command("makemigrations", name="alter_values")

        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0002_alter_values.py")
        )

        # replace this migration with our own that has custom data
        # migrations

        data_edit_functions = """
def migrate_enum_values(apps, schema_editor):

    MigrationTester = apps.get_model(
        "tests_edit_tests",
        "MigrationTester"
    )
    db_alias = schema_editor.connection.alias
    for obj in MigrationTester.objects.using(db_alias).all():
        obj.int_enum = obj.int_enum + 1
        obj.save()


def revert_enum_values(apps, schema_editor):

    MigrationTester = apps.get_model(
        "tests_edit_tests",
        "MigrationTester"
    )
    db_alias = schema_editor.connection.alias
    for obj in MigrationTester.objects.using(db_alias).all():
        obj.int_enum = obj.int_enum - 1
        obj.save()
        \n\n"""

        data_edit_operations = (
            "        migrations.RunPython(migrate_enum_values, revert_enum_values),\n"
        )

        new_contents = ""
        with open(settings.TEST_MIGRATION_DIR / "0002_alter_values.py", "r") as inpt:
            for line in inpt.readlines():
                if "class Migration" in line:
                    new_contents += data_edit_functions
                if "migrations.AddConstraint(" in line:
                    new_contents += data_edit_operations
                new_contents += line

        with open(settings.TEST_MIGRATION_DIR / "0002_alter_values.py", "w") as output:
            output.write(new_contents)

        migration = import_migration(
            settings.TEST_MIGRATION_DIR / "0002_alter_values.py"
        )

        self.assertIsInstance(migration.operations[0], migrations.RemoveConstraint)
        self.assertIsInstance(migration.operations[-1], migrations.AddConstraint)
        self.assertEqual(
            getattr(migration.operations[-1].constraint, condition),
            Q(int_enum__in=[1, 2, 3]),
        )
        self.assertEqual(
            migration.operations[-1].constraint.name,
            "tests_edit_tests_MigrationTester_int_enum_IntEnum",
        )

    def test_makemigrate_03(self):
        from django.conf import settings

        set_models(3)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0003_remove_black.py")
        )

        call_command("makemigrations", name="remove_black")

        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0003_remove_black.py")
        )

        data_edit_functions = """
def remove_color_values(apps, schema_editor):

    MigrationTester = apps.get_model(
        "tests_edit_tests",
        "MigrationTester"
    )
    db_alias = schema_editor.connection.alias
    MigrationTester.objects.using(db_alias).filter(color='K').delete()
        
\n"""
        data_edit_operations = "        migrations.RunPython(remove_color_values, migrations.RunPython.noop),\n"

        new_contents = ""
        with open(settings.TEST_MIGRATION_DIR / "0003_remove_black.py", "r") as inpt:
            for line in inpt.readlines():
                if "class Migration" in line:
                    new_contents += data_edit_functions
                if "migrations.AddConstraint(" in line:
                    new_contents += data_edit_operations
                new_contents += line

        with open(settings.TEST_MIGRATION_DIR / "0003_remove_black.py", "w") as output:
            output.write(new_contents)

        migration = import_migration(
            settings.TEST_MIGRATION_DIR / "0003_remove_black.py"
        )
        self.assertIsInstance(migration.operations[0], migrations.RemoveConstraint)
        self.assertIsInstance(migration.operations[-1], migrations.AddConstraint)
        self.assertEqual(
            getattr(migration.operations[-1].constraint, condition),
            Q(color__in=["R", "G", "B"]),
        )
        self.assertEqual(
            migration.operations[-1].constraint.name,
            "tests_edit_tests_MigrationTester_color_Color",
        )

    def test_makemigrate_04(self):
        from django.conf import settings

        set_models(4)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0004_change_names.py")
        )

        call_command("makemigrations", name="change_names")

        # should not exist!
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0004_change_names.py")
        )

    def test_makemigrate_05(self):
        from django.conf import settings

        set_models(5)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0004_remove_constraint.py")
        )

        call_command("makemigrations", name="remove_constraint")

        # should not exist!
        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0004_remove_constraint.py")
        )

        with open(
            settings.TEST_MIGRATION_DIR / "0004_remove_constraint.py", "r"
        ) as inpt:
            contents = inpt.read()
            self.assertEqual(contents.count("RemoveConstraint"), 1)
            self.assertEqual(contents.count("AddConstraint"), 0)

    def test_makemigrate_06(self):
        from django.conf import settings

        set_models(6)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0005_expand_int_enum.py")
        )

        call_command("makemigrations", name="expand_int_enum")

        # should exist!
        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0005_expand_int_enum.py")
        )

    def test_makemigrate_07(self):
        from django.conf import settings

        set_models(7)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0006_remove_int_enum.py")
        )

        call_command("makemigrations", name="remove_int_enum")

        # should exist!
        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0006_remove_int_enum.py")
        )

    def test_makemigrate_08(self):
        from django.conf import settings

        set_models(8)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0007_add_int_enum.py")
        )

        call_command("makemigrations", name="add_int_enum")

        # should exist!
        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0007_add_int_enum.py")
        )

        migration = import_migration(
            settings.TEST_MIGRATION_DIR / "0007_add_int_enum.py"
        )
        self.assertIsInstance(migration.operations[0], migrations.RemoveConstraint)
        self.assertIsInstance(migration.operations[3], migrations.AddConstraint)
        self.assertIsInstance(migration.operations[4], migrations.AddConstraint)
        self.assertEqual(
            getattr(migration.operations[3].constraint, condition),
            Q(int_enum__in=["A", "B", "C"]) | Q(int_enum__isnull=True),
        )
        self.assertEqual(
            getattr(migration.operations[4].constraint, condition),
            Q(color__in=["R", "G", "B", "K"]),
        )
        self.assertEqual(
            migration.operations[3].constraint.name,
            "tests_edit_tests_MigrationTester_int_enum_IntEnum",
        )
        self.assertEqual(
            migration.operations[4].constraint.name,
            "tests_edit_tests_MigrationTester_color_Color",
        )

    def test_makemigrate_09(self):
        from django.conf import settings

        set_models(9)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0008_set_default.py")
        )

        call_command("makemigrations", name="set_default")

        # should exist!
        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0008_set_default.py")
        )

    def test_makemigrate_10(self):
        from django.conf import settings

        set_models(10)
        self.assertFalse(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0009_change_default.py")
        )

        call_command("makemigrations", name="change_default")

        # should exist!
        self.assertTrue(
            os.path.isfile(settings.TEST_MIGRATION_DIR / "0009_change_default.py")
        )


class TestInitialMigration(ResetModelsMixin, MigratorTestCase):
    migrate_from = ("tests_edit_tests", "0001_initial")
    migrate_to = ("tests_edit_tests", "0001_initial")

    @classmethod
    def setUpClass(cls):
        set_models(1)
        super().setUpClass()

    def test_0001_initial(self):
        MigrationTester = self.new_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (0, "R"),
            (1, "G"),
            (2, "B"),
            (0, "K"),
        ]:
            MigrationTester.objects.create(int_enum=int_enum, color=color)

        self.assertEqual(len(MigrationTester._meta.get_fields()), 3)
        self.assertEqual(MigrationTester.objects.filter(int_enum=0).count(), 2)
        self.assertEqual(MigrationTester.objects.filter(int_enum=1).count(), 1)
        self.assertEqual(MigrationTester.objects.filter(int_enum=2).count(), 1)

        self.assertEqual(MigrationTester.objects.filter(color="R").count(), 1)
        self.assertEqual(MigrationTester.objects.filter(color="G").count(), 1)
        self.assertEqual(MigrationTester.objects.filter(color="B").count(), 1)
        self.assertEqual(MigrationTester.objects.filter(color="K").count(), 1)

        # todo the constraints are failing these tests because they are
        #   changed before the data is changed - these tests need to be
        #   updated to change the data between the constraint changes

    def test_0001_code(self):
        from .edit_tests.models import MigrationTester

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (MigrationTester.IntEnum(0), MigrationTester.Color((1, 0, 0))),
            (MigrationTester.IntEnum["TWO"], MigrationTester.Color("00FF00")),
            (MigrationTester.IntEnum.THREE, MigrationTester.Color("Blue")),
            (MigrationTester.IntEnum.ONE, MigrationTester.Color.BLACK),
        ]:
            MigrationTester.objects.create(int_enum=int_enum, color=color)

        for obj in MigrationTester.objects.all():
            self.assertIsInstance(obj.int_enum, MigrationTester.IntEnum)
            self.assertIsInstance(obj.color, MigrationTester.Color)

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum.ONE
            ).count(),
            2,
        )
        self.assertEqual(
            MigrationTester.objects.filter(int_enum=MigrationTester.IntEnum(1)).count(),
            1,
        )
        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum["THREE"]
            ).count(),
            1,
        )

        self.assertEqual(MigrationTester.objects.filter(color=(1, 0, 0)).count(), 1)
        self.assertEqual(MigrationTester.objects.filter(color="GREEN").count(), 1)
        self.assertEqual(MigrationTester.objects.filter(color="Blue").count(), 1)
        self.assertEqual(MigrationTester.objects.filter(color="000000").count(), 1)

        MigrationTester.objects.all().delete()


class TestAlterValuesMigration(ResetModelsMixin, MigratorTestCase):
    migrate_from = ("tests_edit_tests", "0001_initial")
    migrate_to = ("tests_edit_tests", "0002_alter_values")

    @classmethod
    def setUpClass(cls):
        set_models(2)
        super().setUpClass()

    def prepare(self):
        MigrationTester = self.old_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (0, "R"),
            (1, "G"),
            (2, "B"),
            (0, "K"),
        ]:
            MigrationTester.objects.create(int_enum=int_enum, color=color)

    def test_0002_alter_values(self):
        MigrationTesterNew = self.new_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=0).count(), 0)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=1).count(), 2)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=2).count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=3).count(), 1)

        self.assertEqual(MigrationTesterNew.objects.filter(color="R").count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color="G").count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color="B").count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color="K").count(), 1)

    def test_0002_code(self):
        from .edit_tests.models import MigrationTester

        MigrationTester.objects.all().delete()

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (MigrationTester.IntEnum(1), MigrationTester.Color((1, 0, 0))),
            (MigrationTester.IntEnum["TWO"], MigrationTester.Color("00FF00")),
            (MigrationTester.IntEnum.THREE, MigrationTester.Color("Blue")),
            (MigrationTester.IntEnum.ONE, MigrationTester.Color.BLACK),
        ]:
            MigrationTester.objects.create(int_enum=int_enum, color=color)

        for obj in MigrationTester.objects.all():
            self.assertIsInstance(obj.int_enum, MigrationTester.IntEnum)
            self.assertIsInstance(obj.color, MigrationTester.Color)

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum.ONE, color=(1, 0, 0)
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum.ONE,
                color=MigrationTester.Color.BLACK,
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum(2), color="GREEN"
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(int_enum=3, color="Blue").count(), 1
        )

        MigrationTester.objects.all().delete()


class TestRemoveBlackMigration(ResetModelsMixin, MigratorTestCase):
    migrate_from = ("tests_edit_tests", "0002_alter_values")
    migrate_to = ("tests_edit_tests", "0003_remove_black")

    @classmethod
    def setUpClass(cls):
        set_models(3)
        super().setUpClass()

    def prepare(self):
        MigrationTester = self.old_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (1, "R"),
            (2, "G"),
            (3, "B"),
            (1, "K"),
        ]:
            MigrationTester.objects.create(int_enum=int_enum, color=color)

    def test_0003_remove_black(self):
        MigrationTesterNew = self.new_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=0).count(), 0)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=1).count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=2).count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum=3).count(), 1)

        self.assertEqual(MigrationTesterNew.objects.filter(color="R").count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color="G").count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color="B").count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color="K").count(), 0)

    def test_0003_code(self):
        from .edit_tests.models import MigrationTester

        MigrationTester.objects.all().delete()

        self.assertFalse(hasattr(MigrationTester.Color, "BLACK"))

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (MigrationTester.IntEnum(1), MigrationTester.Color((1, 0, 0))),
            (MigrationTester.IntEnum["TWO"], MigrationTester.Color("00FF00")),
            (MigrationTester.IntEnum.THREE, MigrationTester.Color("Blue")),
        ]:
            MigrationTester.objects.create(int_enum=int_enum, color=color)

        for obj in MigrationTester.objects.all():
            self.assertIsInstance(obj.int_enum, MigrationTester.IntEnum)
            self.assertIsInstance(obj.color, MigrationTester.Color)

        self.assertEqual(MigrationTester.objects.count(), 3)

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum.ONE, color=(1, 0, 0)
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum(2), color="GREEN"
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(int_enum=3, color="Blue").count(), 1
        )

        MigrationTester.objects.all().delete()


class TestConstrainedButNonStrict(ResetModelsMixin, MigratorTestCase):
    migrate_from = ("tests_edit_tests", "0002_alter_values")
    migrate_to = ("tests_edit_tests", "0003_remove_black")

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
            color="R",
        )


class TestRemoveConstraintMigration(ResetModelsMixin, MigratorTestCase):
    migrate_from = ("tests_edit_tests", "0003_remove_black")
    migrate_to = ("tests_edit_tests", "0004_remove_constraint")

    @classmethod
    def setUpClass(cls):
        set_models(5)
        super().setUpClass()

    def test_remove_contraint_code(self):
        # no migration was generated for this model class change
        from django.db.models import PositiveSmallIntegerField

        from .edit_tests.models import MigrationTester

        MigrationTester.objects.all().delete()

        for int_enum, color in [
            (MigrationTester.IntEnum.ONE, MigrationTester.Color.RD),
            (MigrationTester.IntEnum(2), MigrationTester.Color("GR")),
            (MigrationTester.IntEnum["THREE"], MigrationTester.Color("0000ff")),
            (42, MigrationTester.Color("Blue")),
        ]:
            MigrationTester.objects.create(int_enum=int_enum, color=color)

        for obj in MigrationTester.objects.all():
            if obj.int_enum != 42:
                self.assertIsInstance(obj.int_enum, MigrationTester.IntEnum)
            self.assertIsInstance(obj.color, MigrationTester.Color)

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum(1),
                color=MigrationTester.Color("RD"),
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum.TWO,
                color=MigrationTester.Color((0, 1, 0)),
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum["THREE"],
                color=MigrationTester.Color("Blue"),
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=42, color=MigrationTester.Color("Blue")
            ).count(),
            1,
        )
        self.assertEqual(MigrationTester.objects.get(int_enum=42).int_enum, 42)

        self.assertEqual(MigrationTester.objects.count(), 4)

        MigrationTester.objects.all().delete()

        self.assertIsInstance(
            MigrationTester._meta.get_field("int_enum"),
            PositiveSmallIntegerField,
        )


class TestExpandIntEnumMigration(ResetModelsMixin, MigratorTestCase):
    migrate_from = ("tests_edit_tests", "0003_remove_black")
    migrate_to = ("tests_edit_tests", "0005_expand_int_enum")

    @classmethod
    def setUpClass(cls):
        set_models(6)
        super().setUpClass()

    def prepare(self):
        from django.db.utils import DatabaseError

        MigrationTester = self.old_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (1, "R"),
            (2, "G"),
            (3, "B"),
        ]:
            MigrationTester.objects.create(int_enum=int_enum, color=color)

        with self.assertRaises(DatabaseError):
            MigrationTester.objects.create(int_enum=32768, color="B")

    def test_0005_expand_int_enum(self):
        from django.core.exceptions import FieldDoesNotExist, FieldError
        from django.db.models import PositiveIntegerField

        MigrationTesterNew = self.new_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        self.assertIsInstance(
            MigrationTesterNew._meta.get_field("int_enum"), PositiveIntegerField
        )

    def test_0005_code(self):
        from .edit_tests.models import MigrationTester

        MigrationTester.objects.create(int_enum=32768, color="B")
        self.assertEqual(MigrationTester.objects.filter(int_enum=32768).count(), 1)
        self.assertEqual(MigrationTester.objects.count(), 4)


class TestRemoveIntEnumMigration(ResetModelsMixin, MigratorTestCase):
    migrate_from = ("tests_edit_tests", "0005_expand_int_enum")
    migrate_to = ("tests_edit_tests", "0006_remove_int_enum")

    @classmethod
    def setUpClass(cls):
        set_models(7)
        super().setUpClass()

    def prepare(self):
        MigrationTester = self.old_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        # Let's create a model with just a single field specified:
        for int_enum, color in [
            (1, "R"),
            (2, "G"),
            (3, "B"),
        ]:
            MigrationTester.objects.create(int_enum=int_enum, color=color)

    def test_0006_remove_int_enum(self):
        from django.core.exceptions import FieldDoesNotExist, FieldError

        MigrationTesterNew = self.new_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        self.assertRaises(
            FieldDoesNotExist, MigrationTesterNew._meta.get_field, "int_num"
        )
        self.assertRaises(
            FieldError, MigrationTesterNew.objects.filter, {"int_enum": 1}
        )

    def test_0006_code(self):
        from .edit_tests.models import MigrationTester

        MigrationTester.objects.all().delete()

        for color in [
            MigrationTester.Color.RD,
            MigrationTester.Color("GR"),
            MigrationTester.Color("0000ff"),
        ]:
            MigrationTester.objects.create(color=color)

        for obj in MigrationTester.objects.all():
            self.assertFalse(hasattr(obj, "int_enum"))
            self.assertIsInstance(obj.color, MigrationTester.Color)

        self.assertEqual(
            MigrationTester.objects.filter(color=MigrationTester.Color("RD")).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(
                color=MigrationTester.Color((0, 1, 0))
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(color=MigrationTester.Color("Blue")).count(),
            1,
        )

        self.assertEqual(MigrationTester.objects.count(), 3)

        MigrationTester.objects.all().delete()


class TestAddIntEnumMigration(ResetModelsMixin, MigratorTestCase):
    migrate_from = ("tests_edit_tests", "0006_remove_int_enum")
    migrate_to = ("tests_edit_tests", "0007_add_int_enum")

    @classmethod
    def setUpClass(cls):
        set_models(8)
        super().setUpClass()

    def prepare(self):
        MigrationTester = self.old_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        # Let's create a model with just a single field specified:
        for color in ["R", "G", "B"]:
            MigrationTester.objects.create(color=color)

    def test_0007_add_int_enum(self):
        from django.core.exceptions import FieldDoesNotExist, FieldError

        MigrationTesterNew = self.new_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        self.assertEqual(
            MigrationTesterNew.objects.filter(int_enum__isnull=True).count(), 3
        )

        MigrationTesterNew.objects.filter(color="R").update(int_enum="A")
        MigrationTesterNew.objects.filter(color="G").update(int_enum="B")
        MigrationTesterNew.objects.filter(color="B").update(int_enum="C")

        self.assertEqual(MigrationTesterNew.objects.filter(int_enum="0").count(), 0)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum="1").count(), 0)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum="2").count(), 0)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum="3").count(), 0)

        self.assertEqual(MigrationTesterNew.objects.filter(int_enum="A").count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum="B").count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(int_enum="C").count(), 1)

        self.assertEqual(MigrationTesterNew.objects.filter(color="R").count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color="G").count(), 1)
        self.assertEqual(MigrationTesterNew.objects.filter(color="B").count(), 1)

    def test_0007_code(self):
        from .edit_tests.models import MigrationTester

        MigrationTester.objects.all().delete()

        for int_enum, color in [
            (MigrationTester.IntEnum.A, MigrationTester.Color.RED),
            (MigrationTester.IntEnum("B"), MigrationTester.Color("Green")),
            (MigrationTester.IntEnum["C"], MigrationTester.Color("0000ff")),
        ]:
            MigrationTester.objects.create(int_enum=int_enum, color=color)

        for obj in MigrationTester.objects.all():
            self.assertIsInstance(obj.int_enum, MigrationTester.IntEnum)
            self.assertIsInstance(obj.color, MigrationTester.Color)

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum("A"),
                color=MigrationTester.Color("Red"),
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum.B,
                color=MigrationTester.Color((0, 1, 0)),
            ).count(),
            1,
        )

        self.assertEqual(
            MigrationTester.objects.filter(
                int_enum=MigrationTester.IntEnum["C"],
                color=MigrationTester.Color("BLUE"),
            ).count(),
            1,
        )

        self.assertEqual(MigrationTester.objects.count(), 3)

        self.assertRaises(
            ValueError,
            MigrationTester.objects.create,
            int_enum="D",
            color=MigrationTester.Color("Blue"),
        )

        MigrationTester.objects.all().delete()


class TestChangeDefaultIndirectlyMigration(ResetModelsMixin, MigratorTestCase):
    migrate_from = ("tests_edit_tests", "0008_set_default")
    migrate_to = ("tests_edit_tests", "0009_change_default")

    @classmethod
    def setUpClass(cls):
        set_models(9)
        super().setUpClass()

    def prepare(self):
        MigrationTester = self.old_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        MigrationTester.objects.create()

    def test_0009_change_default(self):
        from django.core.exceptions import FieldDoesNotExist, FieldError

        MigrationTesterNew = self.new_state.apps.get_model(
            "tests_edit_tests", "MigrationTester"
        )

        self.assertEqual(MigrationTesterNew.objects.first().color, "K")

        self.assertEqual(MigrationTesterNew.objects.create().color, "B")


def test_migration_test_marker_tag():
    """Ensure ``MigratorTestCase`` sublasses are properly tagged."""
    assert MIGRATION_TEST_MARKER in TestInitialMigration.tags
    assert MIGRATION_TEST_MARKER in TestAlterValuesMigration.tags
    assert MIGRATION_TEST_MARKER in TestRemoveBlackMigration.tags
    assert MIGRATION_TEST_MARKER in TestRemoveIntEnumMigration.tags
    assert MIGRATION_TEST_MARKER in TestAddIntEnumMigration.tags
