.. include:: ../refs.rst

.. _external:

==================
Use External Enums
==================

:class:`enum.Enum` classes defined externally to your code base or enum classes that otherwise do
not inherit from Django's :ref:`field-choices-enum-types`, are supported. When no choices are
present on an :class:`enum.Enum` type, :class:`~django_enum.fields.EnumField` will attempt to use
the ``label`` member on each enumeration value if it is present, otherwise the labels will be based
off the enumeration name. Choices can also be overridden at the
:class:`~django_enum.fields.EnumField` declaration.

:class:`~django_enum.fields.EnumField` should work with any subclass of :class:`enum.Enum`.

.. literalinclude:: ../../../tests/examples/models/extern.py

The list of choice tuples for each field are:

.. literalinclude:: ../../../tests/examples/extern_howto.py
    :lines: 3-

.. warning::

    One nice feature of Django's :ref:`field-choices-enum-types` are that they disable
    :class:`enum.auto` on :class:`enum.Enum` fields. :class:`enum.auto` can be dangerous because the
    values assigned depend on the order of declaration. This means that if the order changes
    existing database values will no longer align with the enumeration values. When control over the
    values is not certain it is a good idea to add integration tests that look for value changes.
