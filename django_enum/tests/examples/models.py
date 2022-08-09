from django.db import models
from django_enum import EnumField, IntegerChoices
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
