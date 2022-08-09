from django.db import models
from django_enum import EnumField, IntegerChoices, TextChoices
from enum_properties import p, s


class Map(models.Model):

    class MapBoxStyle(
        IntegerChoices,
        s('slug', case_fold=True),
        s('label', case_fold=True),
        p('version')
    ):
        """
        https://docs.mapbox.com/api/maps/styles/
        """
        _symmetric_builtins_ = ['name', 'uri']

        # name             value    slug                 label         version
        STREETS           =  1,   'streets',           'Streets',           11
        OUTDOORS          =  2,   'outdoors',          'Outdoors',          11
        LIGHT             =  3,   'light',             'Light',             10
        DARK              =  4,   'dark',              'Dark',              10
        SATELLITE         =  5,   'satellite',         'Satellite',          9
        SATELLITE_STREETS =  6,   'satellite-streets', 'Satellite Streets', 11
        NAVIGATION_DAY    =  7,   'navigation-day',    'Navigation Day',     1
        NAVIGATION_NIGHT  =  8,   'navigation-night',  'Navigation Night',   1

        @property
        def uri(self):
            return f'mapbox://styles/mapbox/{self.slug}-v{self.version}'

        def __str__(self):
            return self.uri

    style = EnumField(MapBoxStyle, default=MapBoxStyle.STREETS)


class StrictExample(models.Model):

    class EnumType(TextChoices):

        ONE = '1', 'One'
        TWO = '2', 'Two'

    non_strict = EnumField(
        EnumType,
        strict=False,
        # it might be necessary to override max_length also, otherwise
        # max_length will be 1
        max_length=10
    )


class NoCoerceExample(models.Model):

    class EnumType(TextChoices):

        ONE = '1', 'One'
        TWO = '2', 'Two'

    non_strict = EnumField(
        EnumType,
        strict=False,
        coerce=False,
        # it might be necessary to override max_length also, otherwise
        # max_length will be 1
        max_length=10
    )


class TextChoicesExample(models.Model):

    class Color(TextChoices, s('rgb'), s('hex', case_fold=True)):

        # name   value   label       rgb       hex
        RED     = 'R',   'Red',   (1, 0, 0), 'ff0000'
        GREEN   = 'G',   'Green', (0, 1, 0), '00ff00'
        BLUE    = 'B',   'Blue',  (0, 0, 1), '0000ff'

        # any named s() values in the Enum's inheritance become properties on
        # each value, and the enumeration value may be instantiated from the
        # property's value

    color = EnumField(Color)


class MyModel(models.Model):

    class TextEnum(models.TextChoices):

        VALUE0 = 'V0', 'Value 0'
        VALUE1 = 'V1', 'Value 1'
        VALUE2 = 'V2', 'Value 2'

    class IntEnum(models.IntegerChoices):

        ONE   = 1, 'One'
        TWO   = 2, 'Two',
        THREE = 3, 'Three'

    # this is equivalent to:
    #  CharField(max_length=2, choices=TextEnum.choices, null=True, blank=True)
    txt_enum = EnumField(TextEnum, null=True, blank=True)

    # this is equivalent to
    #  PositiveSmallIntegerField(choices=IntEnum.choices)
    int_enum = EnumField(IntEnum)
