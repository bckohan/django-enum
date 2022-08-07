# Generated by Django 3.2.14 on 2022-07-26 03:42

import django_enum.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EnumTester',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('small_pos_int', django_enum.fields.EnumPositiveSmallIntegerField(blank=True, choices=[(0, 'Value 1'), (2, 'Value 2'), (32767, 'Value 32767')], db_index=True, default=None, null=True)),
                ('small_int', django_enum.fields.EnumSmallIntegerField(blank=True, choices=[(-32768, 'Value -32768'), (0, 'Value 0'), (1, 'Value 1'), (2, 'Value 2'), (32767, 'Value 32767')], db_index=True, default=32767)),
                ('pos_int', django_enum.fields.EnumPositiveIntegerField(blank=True, choices=[(0, 'Value 0'), (1, 'Value 1'), (2, 'Value 2'), (2147483647, 'Value 2147483647')], db_index=True, default=2147483647)),
                ('int', django_enum.fields.EnumIntegerField(blank=True, choices=[(-2147483648, 'Value -2147483648'), (0, 'Value 0'), (1, 'Value 1'), (2, 'Value 2'), (2147483647, 'Value 2147483647')], db_index=True, null=True)),
                ('big_pos_int', django_enum.fields.EnumPositiveBigIntegerField(blank=True, choices=[(0, 'Value 0'), (1, 'Value 1'), (2, 'Value 2'), (2147483648, 'Value 2147483647')], db_index=True, default=None, null=True)),
                ('big_int', django_enum.fields.EnumBigIntegerField(blank=True, choices=[(-2147483649, 'Value -2147483649'), (1, 'Value 1'), (2, 'Value 2'), (2147483648, 'Value 2147483647')], db_index=True, default=-2147483649)),
                ('constant', django_enum.fields.EnumFloatField(blank=True, choices=[(3.141592653589793, 'Pi'), (2.71828, "Euler's Number"), (1.618033988749895, 'Golden Ratio')], db_index=True, default=None, null=True)),
                ('text', django_enum.fields.EnumCharField(blank=True, choices=[('V1', 'Value1'), ('V22', 'Value2'), ('V333', 'Value3'), ('D', 'Default')], db_index=True, default=None, max_length=4, null=True)),
                ('int_choice', models.IntegerField(blank=True, choices=[(1, 'One'), (2, 'Two'), (3, 'Three')], default=1)),
                ('char_choice', models.CharField(blank=True, choices=[('A', 'First'), ('B', 'Second'), ('C', 'Third')], default='A', max_length=1)),
                ('int_field', models.IntegerField(blank=True, default=1)),
                ('float_field', models.FloatField(blank=True, default=1.5)),
                ('char_field', models.CharField(blank=True, default='A', max_length=1)),
                ('dj_int_enum', django_enum.fields.EnumPositiveSmallIntegerField(choices=[(1, 'One'), (2, 'Two'), (3, 'Three')], default=1)),
                ('dj_text_enum', django_enum.fields.EnumCharField(choices=[('A', 'Label A'), ('B', 'Label B'), ('C', 'Label C')], default='A', max_length=1)),
                ('non_strict_int', django_enum.fields.EnumPositiveSmallIntegerField(blank=True, choices=[(0, 'Value 1'), (2, 'Value 2'), (32767, 'Value 32767')], default=None, null=True)),
            ],
            options={
                'ordering': ('id',),
            },
        ),
    ]
