# Generated by Django 5.0.2 on 2024-03-03 06:40

import django.db.models.functions.text
import django_enum.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DBDefaultTester",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "small_pos_int",
                    django_enum.fields.EnumPositiveSmallIntegerField(
                        blank=True,
                        choices=[
                            (0, "Value 1"),
                            (2, "Value 2"),
                            (32767, "Value 32767"),
                        ],
                        db_default=None,
                        null=True,
                    ),
                ),
                (
                    "small_int",
                    django_enum.fields.EnumSmallIntegerField(
                        blank=True,
                        choices=[
                            (-32768, "Value -32768"),
                            (0, "Value 0"),
                            (1, "Value 1"),
                            (2, "Value 2"),
                            (32767, "Value 32767"),
                        ],
                        db_default=32767,
                    ),
                ),
                (
                    "pos_int",
                    django_enum.fields.EnumPositiveIntegerField(
                        blank=True,
                        choices=[
                            (0, "Value 0"),
                            (1, "Value 1"),
                            (2, "Value 2"),
                            (2147483647, "Value 2147483647"),
                        ],
                        db_default=2147483647,
                    ),
                ),
                (
                    "int",
                    django_enum.fields.EnumIntegerField(
                        blank=True,
                        choices=[
                            (-2147483648, "Value -2147483648"),
                            (0, "Value 0"),
                            (1, "Value 1"),
                            (2, "Value 2"),
                            (2147483647, "Value 2147483647"),
                        ],
                        db_default=-2147483648,
                        null=True,
                    ),
                ),
                (
                    "big_pos_int",
                    django_enum.fields.EnumPositiveBigIntegerField(
                        blank=True,
                        choices=[
                            (0, "Value 0"),
                            (1, "Value 1"),
                            (2, "Value 2"),
                            (2147483648, "Value 2147483648"),
                        ],
                        db_default=None,
                        null=True,
                    ),
                ),
                (
                    "big_int",
                    django_enum.fields.EnumBigIntegerField(
                        blank=True,
                        choices=[
                            (-2147483649, "Value -2147483649"),
                            (1, "Value 1"),
                            (2, "Value 2"),
                            (2147483648, "Value 2147483648"),
                        ],
                        db_default=-2147483649,
                    ),
                ),
                (
                    "constant",
                    django_enum.fields.EnumFloatField(
                        blank=True,
                        choices=[
                            (3.141592653589793, "Pi"),
                            (2.71828, "Euler's Number"),
                            (1.618033988749895, "Golden Ratio"),
                        ],
                        db_default=1.618033988749895,
                        null=True,
                    ),
                ),
                (
                    "text",
                    django_enum.fields.EnumCharField(
                        blank=True,
                        choices=[
                            ("V1", "Value1"),
                            ("V22", "Value2"),
                            ("V333", "Value3"),
                            ("D", "Default"),
                        ],
                        db_default="",
                        max_length=4,
                    ),
                ),
                (
                    "doubled_text",
                    django_enum.fields.EnumCharField(
                        blank=True,
                        choices=[
                            ("V1", "Value1"),
                            ("V22", "Value2"),
                            ("V333", "Value3"),
                            ("D", "Default"),
                        ],
                        db_default=django.db.models.functions.text.Concat(
                            models.Value("db"), models.Value("_default")
                        ),
                        default="",
                        max_length=10,
                    ),
                ),
                (
                    "doubled_text_strict",
                    django_enum.fields.EnumCharField(
                        blank=True,
                        choices=[
                            ("V1", "Value1"),
                            ("V22", "Value2"),
                            ("V333", "Value3"),
                            ("D", "Default"),
                        ],
                        db_default="V22",
                        default="D",
                        max_length=10,
                    ),
                ),
                (
                    "char_field",
                    models.CharField(
                        blank=True, db_default="db_default", max_length=10
                    ),
                ),
                (
                    "doubled_char_field",
                    models.CharField(
                        blank=True,
                        db_default="db_default",
                        default="default",
                        max_length=10,
                    ),
                ),
                (
                    "extern",
                    django_enum.fields.EnumPositiveSmallIntegerField(
                        blank=True,
                        choices=[(1, "ONE"), (2, "TWO"), (3, "THREE")],
                        db_default=3,
                        null=True,
                    ),
                ),
                (
                    "dj_int_enum",
                    django_enum.fields.EnumPositiveSmallIntegerField(
                        choices=[(1, "One"), (2, "Two"), (3, "Three")], db_default=1
                    ),
                ),
                (
                    "dj_text_enum",
                    django_enum.fields.EnumCharField(
                        choices=[("A", "Label A"), ("B", "Label B"), ("C", "Label C")],
                        db_default="A",
                        max_length=1,
                    ),
                ),
                (
                    "non_strict_int",
                    django_enum.fields.EnumPositiveSmallIntegerField(
                        blank=True,
                        choices=[
                            (0, "Value 1"),
                            (2, "Value 2"),
                            (32767, "Value 32767"),
                        ],
                        db_default=5,
                        null=True,
                    ),
                ),
                (
                    "non_strict_text",
                    django_enum.fields.EnumCharField(
                        blank=True,
                        choices=[
                            ("V1", "Value1"),
                            ("V22", "Value2"),
                            ("V333", "Value3"),
                            ("D", "Default"),
                        ],
                        db_default="arbitrary",
                        max_length=12,
                    ),
                ),
                (
                    "no_coerce",
                    django_enum.fields.EnumPositiveSmallIntegerField(
                        blank=True,
                        choices=[
                            (0, "Value 1"),
                            (2, "Value 2"),
                            (32767, "Value 32767"),
                        ],
                        db_default=2,
                        null=True,
                    ),
                ),
                (
                    "no_coerce_value",
                    django_enum.fields.EnumPositiveSmallIntegerField(
                        blank=True,
                        choices=[
                            (0, "Value 1"),
                            (2, "Value 2"),
                            (32767, "Value 32767"),
                        ],
                        db_default=32767,
                        null=True,
                    ),
                ),
                (
                    "no_coerce_none",
                    django_enum.fields.EnumPositiveSmallIntegerField(
                        blank=True,
                        choices=[
                            (0, "Value 1"),
                            (2, "Value 2"),
                            (32767, "Value 32767"),
                        ],
                        db_default=None,
                        null=True,
                    ),
                ),
            ],
            options={
                "ordering": ("id",),
            },
        ),
    ]
