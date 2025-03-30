.. include:: ../refs.rst

.. _integrations:

==================
Integrate with ...
==================

.. tip::

    :class:`~django_enum.fields.EnumField` instances ultimately inherit from existing core Django_
    model fields and set the :ref:`choices attribute <field-choices>`. Therefore
    :class:`~django_enum.fields.EnumField` *should work with any third party libraries and will
    behave as a core field with a defined choice tuple list would*.

However, you may want to take advantage of some of the extra features provided by django-enum_. We
provide out-of-the-box integration with the following libraries:

.. _enum_props:

enum-properties
---------------

Almost any :class:`enum.Enum` type is supported, so you may make use of :class:`enum.Enum`
extension libraries like :doc:`enum-properties <enum-properties:index>` to define very rich
enumeration fields. You will need to install the properties optional dependency set:

.. code:: bash

       pip install "django-enum[properties]"

:doc:`enum-properties <enum-properties:index>` is an extension to :class:`enum.Enum` that allows
properties to be added to enumeration instances using a simple declarative syntax. This is a less
awkward and more compatible alternative to :mod:`dataclass enumerations <dataclasses>`.

If you find yourself considering a :mod:`dataclass enumeration <dataclasses>`, consider using
:doc:`enum-properties <enum-properties:index>` instead. Dataclass value types do not work with
:class:`~django_enum.fields.EnumField`. Most libraries that work with enumerations expect the
:attr:`~enum.Enum.value` attribute to be a primitive serializable type.

:doc:`enum-properties <enum-properties:index>` also allows for
:ref:`symmetric properties <enum-properties:howto_symmetric_properties>` which compare as equivalent
to the enumeration values and can be used to instantiate enumeration instances.

**For a real-world example see the** :ref:`properties tutorial <properties>`.

It should be unnecessary, but if you need to integrate with code that expects an interface fully
compatible with Django's
`enumeration types <https://docs.djangoproject.com/en/stable/ref/models/fields/#enumeration-types>`_
(``TextChoices`` and ``IntegerChoices`` django-enum_ provides
:class:`~django_enum.choices.TextChoices`, :class:`~django_enum.choices.IntegerChoices`,
:class:`~django_enum.choices.FlagChoices` and :class:`~django_enum.choices.FloatChoices` types that
derive from :doc:`enum-properties <enum-properties:index>` and Django's ``Choices``. For instance,
you may be using a third party library that uses :func:`isinstance` checks on your enum types
instead of duck typing. For compatibility in these cases simply use django-enum_'s ``Choices`` types
as the base class for your enumeration instead:

.. literalinclude:: ../../../tests/examples/models/text_choices.py
    :lines: 2-

All of the expected :doc:`enum-properties <enum-properties:index>` behavior works:

.. literalinclude:: ../../../tests/examples/text_choices_howto.py
    :lines: 4-

.. note::

    To make your non-choices derived enum :ref:`quack like one <field-choices>`, you will need to
    add:

        1. a ``choices`` property that returns the choices tuple list
        2. a ``label`` property that returns the list of labels
        3. a ``name`` property that returns the list of names
        4. a ``value`` property that returns the list of values


.. _rest_framework:

Django Rest Framework
---------------------

By default `DRF ModelSerializer
<https://www.django-rest-framework.org/api-guide/serializers/#modelserializer>`_ will use a
`ChoiceField <https://www.django-rest-framework.org/api-guide/fields/#choicefield>`_ to represent an
:class:`~django_enum.fields.EnumField`. This works great, but it will not accept :ref:`symmetric
enumeration values <enum-properties:howto_symmetric_properties>`. A serializer field
:class:`django_enum.drf.EnumField` is provided that will. :class:`~django_enum.fields.FlagField`
fields do not work well with DRF's builtin
`MultipleChoiceField <https://www.django-rest-framework.org/api-guide/fields/#multiplechoicefield>`_
so we also provide a :class:`django_enum.drf.FlagField`.

The dependency on DRF_ is optional so to use the provided serializer field you must install DRF_:


.. code:: bash

    pip install djangorestframework


.. literalinclude:: ../../../tests/examples/drf_serializer_howto.py
    :lines: 3-



The serializer :class:`django_enum.drf.EnumField` accepts any arguments that
`ChoiceField <https://www.django-rest-framework.org/api-guide/fields/#choicefield>`_ does. It also
accepts the ``strict`` parameter which behaves the same way as it does on the model field.

.. tip::

    You only need to use :class:`django_enum.drf.EnumField` if:

    1. You are integrating with :doc:`enum-properties <enum-properties:index>` and want symmetric
       properties to work.
    2. You have non-strict model fields and want to allow your API to accept values outside of
       the enumeration.

The :class:`django_enum.drf.EnumField` must be used for any :class:`~django_enum.fields.FlagField`
fields. It will accept a composite integer or a list of any values coercible to a flag. The
serialized output will be an composite integer holding the full bitfield.

ModelSerializers
~~~~~~~~~~~~~~~~

An :class:`django_enum.drf.EnumFieldMixin` class is provided that when added to
`ModelSerializers <https://www.django-rest-framework.org/api-guide/serializers/#modelserializer>`_
will be sure that the serializer instantiates the correct django-enum serializer field type:

.. literalinclude:: ../../../tests/examples/drf_modelserializer_howto.py
    :lines: 3-

.. _filtering:

django-filter
-------------

As shown above, filtering by any value, enumeration type instance or symmetric value works with
:doc:`Django's ORM <django:topics/db/queries>`. This is not natively true for the default
:class:`django_filters.filterset.FilterSet` from :doc:`django-filter <django-filter:index>`.
Those filter sets will only be filterable by direct enumeration value by default. An
:class:`~django_enum.filters.EnumFilter` class is provided to enable filtering by symmetric property
values, but since the dependency on :doc:`django-filter <django-filter:index>` is optional, you must
first install it:

.. code:: bash

       pip install django-filter

.. literalinclude:: ../../../tests/examples/filterfield_howto.py
    :lines: 2-

A :class:`~django_enum.filters.FilterSet` class is also provided that uses
:class:`~django_enum.filters.EnumFilter` for :class:`~django_enum.fields.EnumField` by default.
So the above is also equivalent to:

.. literalinclude:: ../../../tests/examples/filterset_howto.py
    :lines: 3-

.. tip::

    :class:`~django_enum.filters.FilterSet` may also be used as a mixin.


FlagFields
~~~~~~~~~~

An :class:`~django_enum.filters.EnumFlagFilter` field for flag fields is also provided:

.. literalinclude:: ../../../tests/examples/flagfilterfield_howto.py
    :lines: 2-
