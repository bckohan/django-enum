try:
    from django.db import models
    from django.urls import reverse
    from django_enum import EnumField, TextChoices
    from django_enum.tests.enum_prop.enums import (
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
    from enum_properties import s


    class EnumTester(models.Model):

        small_pos_int = EnumField(SmallPosIntEnum, null=True, default=None, db_index=True, blank=True)
        small_int = EnumField(SmallIntEnum, null=False, default=SmallIntEnum.VAL3, db_index=True, blank=True)

        pos_int = EnumField(PosIntEnum, default=PosIntEnum.VAL3, db_index=True, blank=True)
        int = EnumField(IntEnum, null=True, db_index=True, blank=True)

        big_pos_int = EnumField(BigPosIntEnum, null=True, default=None, db_index=True, blank=True)
        big_int = EnumField(BigIntEnum, default=BigIntEnum.VAL0, db_index=True, blank=True)

        constant = EnumField(Constants, null=True, default=None, db_index=True, blank=True)

        text = EnumField(TextEnum, null=True, default=None, db_index=True, blank=True)

        # basic choice fields - used to compare behavior
        int_choice = models.IntegerField(
            default=1,
            null=False,
            blank=True,
            choices=((1, 'One'), (2, 'Two'), (3, 'Three'))
        )

        char_choice = models.CharField(
            max_length=1,
            default='A',
            null=False,
            blank=True,
            choices=(('A', 'First'), ('B', 'Second'), ('C', 'Third'))
        )

        int_field = models.IntegerField(
            default=1,
            null=False,
            blank=True
        )

        float_field = models.FloatField(
            default=1.5,
            null=False,
            blank=True
        )

        char_field = models.CharField(
            max_length=1,
            default='A',
            null=False,
            blank=True
        )
        ################################################

        dj_int_enum = EnumField(DJIntEnum, default=DJIntEnum.ONE)
        dj_text_enum = EnumField(DJTextEnum, default=DJTextEnum.A)

        # Non-strict
        non_strict_int = EnumField(
            SmallPosIntEnum,
            strict=False,
            null=True,
            default=None,
            blank=True
        )

        def get_absolute_url(self):
            return reverse('django_enum_tests_enum_prop:enum-detail', kwargs={'pk': self.pk})

        class Meta:
            ordering = ('id',)


    class MyModel(models.Model):

        class TextEnum(models.TextChoices):

            VALUE0 = 'V0', 'Value 0'
            VALUE1 = 'V1', 'Value 1'
            VALUE2 = 'V2', 'Value 2'

        class IntEnum(models.IntegerChoices):

            ONE   = 1, 'One'
            TWO   = 2, 'Two',
            THREE = 3, 'Three'

        class Color(TextChoices, s('rgb'), s('hex', case_fold=True)):
            # name   value   label       rgb       hex
            RED = 'R', 'Red', (1, 0, 0), 'ff0000'
            GREEN = 'G', 'Green', (0, 1, 0), '00ff00'
            BLUE = 'B', 'Blue', (0, 0, 1), '0000ff'

        txt_enum = EnumField(TextEnum, null=True, blank=True)
        int_enum = EnumField(IntEnum)
        color = EnumField(Color)


    class PerfCompare(models.Model):

        small_pos_int = models.PositiveSmallIntegerField(choices=SmallPosIntEnum.choices, null=True, default=None, db_index=True, blank=True)
        small_int = models.SmallIntegerField(choices=SmallIntEnum.choices, null=False, default=SmallIntEnum.VAL3, db_index=True, blank=True)

        pos_int = models.PositiveIntegerField(choices=PosIntEnum.choices, default=PosIntEnum.VAL3, db_index=True, blank=True)
        int = models.IntegerField(choices=IntEnum.choices, null=True, db_index=True, blank=True)

        big_pos_int = models.PositiveBigIntegerField(choices=BigPosIntEnum.choices, null=True, default=None, db_index=True, blank=True)
        big_int = models.BigIntegerField(choices=BigIntEnum.choices, default=BigIntEnum.VAL0, db_index=True, blank=True)

        constant = models.FloatField(choices=Constants.choices, null=True, default=None, db_index=True, blank=True)

        text = models.CharField(choices=TextEnum.choices, max_length=4, null=True, default=None, db_index=True, blank=True)

        # basic choice fields - used to compare behavior
        int_choice = models.IntegerField(
            default=1,
            null=False,
            blank=True,
            choices=((1, 'One'), (2, 'Two'), (3, 'Three'))
        )

        char_choice = models.CharField(
            max_length=1,
            default='A',
            null=False,
            blank=True,
            choices=(('A', 'First'), ('B', 'Second'), ('C', 'Third'))
        )

        int_field = models.IntegerField(
            default=1,
            null=False,
            blank=True
        )

        float_field = models.FloatField(
            default=1.5,
            null=False,
            blank=True
        )

        char_field = models.CharField(
            max_length=1,
            default='A',
            null=False,
            blank=True
        )
        ################################################

        dj_int_enum = models.PositiveSmallIntegerField(choices=DJIntEnum.choices, default=DJIntEnum.ONE.value)
        dj_text_enum = models.CharField(choices=DJTextEnum.choices, default=DJTextEnum.A.value, max_length=1)

        # Non-strict
        non_strict_int = models.PositiveSmallIntegerField(choices=SmallPosIntEnum.choices, null=True, default=None, blank=True)

        class Meta:
            ordering = ('id',)


    class SingleEnumPerf(models.Model):

        small_pos_int = EnumField(enum=SmallPosIntEnum, null=True, default=None, db_index=True, blank=True)


    class SingleFieldPerf(models.Model):

        small_pos_int = models.PositiveSmallIntegerField(choices=SmallPosIntEnum.choices, null=True, default=None, db_index=True, blank=True)

except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass
