.. include:: refs.rst

.. _tutorial:

========
Tutorial
========

Enumerations in Python can provide rich class based interfaces, well suited
to many scenarios. A real world example is presented here that leverages
``IntegerChoices`` integration with :doc:`enum-properties:index` to encapsulate more
information and get our enum to do more work.

Map Box Style
_____________

`Mapbox <https://mapbox.com>`_ is a leading web mapping platform. It comes with
a handful of default map styles. An enumeration is a natural choice to
represent these styles but the styles are complicated by the fact that they are
versioned and that when used as a parameter in the mapbox API they are in a URI
format that is overly verbose for a human friendly user interface.

Each mapbox style enumeration is therefore composed of 4 primary properties. A
a human friendly label for the style, a name slug used in the URI, a version
number for the style and the full URI specification of the style. We might
implement our style enumeration like so:

.. code-block:: python

    import typing as t
    from django.db import models
    from django_enum import EnumField
    from enum_properties import IntEnumProperties, Symmetric

    class Map(models.Model):

        class MapBoxStyle(IntEnumProperties):
            """
            https://docs.mapbox.com/api/maps/styles/
            """
            _symmetric_builtins_ = ['name', 'uri']

            label: t.Annotated[str, Symmetric()]
            slug: t.Annotated[str, Symmetric(case_fold=True)]
            version: int

            # name             value    label                 slug          version
            STREETS           =  1,   'Streets',            'streets',           12
            OUTDOORS          =  2,   'Outdoors',           'outdoors',          12
            LIGHT             =  3,   'Light',              'light',             11
            DARK              =  4,   'Dark',               'dark',              11
            SATELLITE         =  5,   'Satellite',          'satellite',          9
            SATELLITE_STREETS =  6,   'Satellite Streets',  'satellite-streets', 12
            NAVIGATION_DAY    =  7,   'Navigation Day',     'navigation-day',     1
            NAVIGATION_NIGHT  =  8,   'Navigation Night',   'navigation-night',   1

            @property
            def uri(self):
                return f'mapbox://styles/mapbox/{self.slug}-v{self.version}'

            def __str__(self):
                return self.uri

        style = EnumField(MapBoxStyle, default=MapBoxStyle.STREETS)


We've used a small integer as the value of the enumeration to save storage
space. We've also added a symmetric case insensitive slug and a non-symmetric
version property. We do not need to specify the label property because we're
inheriting from Django's Choices type which provides a ``label`` property as
the second element in the value tuple.

The version numbers will increment over time, but we're only concerned with the
most recent versions, so we'll increment their values in this enumeration as
they change. Any version number updates exist only in code and will be picked
up as those persisted values are re-instantiated as ``MapBoxStyle``
enumerations.

The last property we've added is the ``uri`` property. We've added it as
concrete property on the class because it can be created from the slug and
version. We could have specified it in the value tuple but that would be very
verbose and less
`DRY <https://en.wikipedia.org/wiki/Don%27t_repeat_yourself>`_. To make this
property symmetric we added it to the ``_symmetric_builtins_`` list.

We can use our enumeration like so:

.. code-block:: python

    map = Map.objects.create()

    assert map.style.uri == 'mapbox://styles/mapbox/streets-v11'

    # uri's are symmetric
    map.style = 'mapbox://styles/mapbox/light-v10'
    map.full_clean()
    assert map.style is Map.MapBoxStyle.LIGHT
    assert map.style == 3
    assert map.style == 'light'

    # so are labels (also case insensitive)
    map.style = 'satellite streets'
    map.full_clean()
    assert map.style == Map.MapBoxStyle.SATELLITE_STREETS

    # when used in API calls (coerced to strings) - they "do the right thing"
    assert str(map.style) == 'mapbox://styles/mapbox/satellite-streets-v11'
