.. include:: ../refs.rst

.. _properties:

==========
Properties
==========

To run this example, we'll need to install django-enum_ with
:doc:`property support <enum-properties:index>`:

.. code-block:: bash

    > pip install "django-enum[properties]"

MapBox Styles
-------------

`MapBox <https://mapbox.com>`_ is a leading web mapping platform. It comes with a handful of default
`map styles <https://docs.mapbox.com/api/maps/styles/#classic-mapbox-styles>`_. An enumeration is a
natural choice to represent these styles but the styles are complicated by versioning and are
identified by different properties depending on context. When used as a parameter in the MapBox API
they are in URI format, but in our interface we would prefer a more human friendly label, and in
code we prefer the brevity and reliability of an :class:`~enum.Enum` value attribute.

Each MapBox style enumeration is therefore composed of 4 primary properties:

1) A a human friendly label for the style
2) A name slug used in the URI
3) A version number for the style
4) The full URI specification of the style.

Leveraging :class:`~enum_properties.IntEnumProperties` We might implement our style enumeration like
so:

.. literalinclude:: ../../../tests/examples/models/mapbox.py
    :language: python
    :lines: 2-

We've used a small integer as the value of the enumeration to save storage space. We've also added a
symmetric case insensitive slug and a version property.

The version numbers will increment over time, but we're only concerned with the most recent
versions, so we'll increment their values in this enumeration as they change. Any version number
updates exist only in code and will be picked up as those persisted values are re-instantiated as
``MapBoxStyle`` enumerations.

The last property we've added is the ``uri`` property. We've added it as concrete property on the
class because it can be created from the slug and version. We could have specified it in the value
tuple but that would be very verbose and less
`DRY <https://en.wikipedia.org/wiki/Don%27t_repeat_yourself>`_. To make this property symmetric we
decorated it with :func:`~enum_properties.symmetric`.

We can use our enumeration like so:

.. literalinclude:: ../../../tests/examples/mapbox_tutorial.py
    :language: python
    :lines: 3-
