.. include:: refs.rst

.. _eccentric:

===============
Eccentric Enums
===============

Python's :class:`enum.Enum` type is extremely lenient. Enumeration values may be any hashable type
and values of the same enumeration may be of different types.

.. tip::

    We define an eccentric enumeration to be any enumeration where the value type is not a simple
    string or integer or where the enumeration values are not all of the same type.

For use in databases it is recommended to use more strict enumeration types that only allow a single
value type of either string or integer. If additional properties need to be associated with
enumeration values, a library like :doc:`enum-properties:index` should be used to store them on the
enumeration value classes.

However, the goal of django-enum_ is to provide as complete of a bridge as possible between Python
and the database so eccentric enumerations are supported with caveats. The following enumeration
value types are supported out of the box, and map to the obvious
:ref:`model field type <ref/models/fields:field types>`.

* :class:`int`
* :class:`str`
* :class:`float`
* :class:`datetime.date`
* :class:`datetime.datetime`
* :class:`datetime.time`
* :class:`datetime.timedelta`
* :class:`decimal.Decimal`

You should avoid eccentric enums if possible, but there may be some compelling reasons to use them.
For example, for unusual data types it may make sense in situations where the database will be used
in a non-Python context and the enumeration values need to retain their native meaning. Or you may
not have direct control over the enumeration you want to store.

Mixed Value Enumerations
========================

Mixed value enumerations are supported. For example:

.. literalinclude:: ../../tests/examples/models/mixed_value.py
    :language: python


:class:`~django_enum.fields.EnumField` will determine the most appropriate database column type to
store the enumeration by trying each of the supported primitive types in order and selecting the
first one that is symmetrically coercible to and from each enumeration value. ``None`` values are
allowed and do not take part in the primitive type selection. In the above example, the database
column type would default to a string.

.. note::

    If none of the supported primitive types are symmetrically coercible
    :class:`~django_enum.fields.EnumField` will not be able to determine an appropriate column
    type and a :exc:`ValueError` will be raised.

In these cases, or to override the primitive type selection made by
:class:`~django_enum.fields.EnumField`, pass the ``primitive`` parameter. It may be necessary to
extend one of the supported primitives to make it coercible. It may also be necessary
to override the :class:`enum.Enum` class's :meth:`~enum.Enum._missing_` method:

.. literalinclude:: ../../tests/examples/mixed_value_example.py
    :language: python
    :lines: 4-

In the above case since ``None`` is an enumeration value, :class:`~django_enum.fields.EnumField`
will automatically set null=True on the model field.

The above yields::

    obj.eccentric_str=<MixedValueEnum.NONE: None>
    obj.eccentric_float=<MixedValueEnum.NONE: None>
    obj.eccentric_str=<MixedValueEnum.VAL1: 1>
    obj.eccentric_float=<MixedValueEnum.VAL1: 1>
    obj.eccentric_str=<MixedValueEnum.VAL2: '2.0'>
    obj.eccentric_float=<MixedValueEnum.VAL2: '2.0'>
    obj.eccentric_str=<MixedValueEnum.VAL3: 3.0>
    obj.eccentric_float=<MixedValueEnum.VAL3: 3.0>
    obj.eccentric_str=<MixedValueEnum.VAL4: Decimal('4.5')>
    obj.eccentric_float=<MixedValueEnum.VAL4: Decimal('4.5')>

Custom Enum Value Types
=======================

.. warning::
    There is almost certainly a better way to do what you might be trying to do by writing a custom
    enumeration value - for example consider using :doc:`enum-properties:index` to make your
    enumeration types more robust by pushing more of this functionality on the :class:`enum.Enum`
    class itself.

If you must use a custom value type, you can by specifying a symmetrically coercible primitive type.
For example Path is already symmetrically coercible to str so this works:

.. literalinclude:: ../../tests/examples/models/path_value.py
    :language: python


A fully custom value might look like the following contrived example:

.. literalinclude:: ../../tests/examples/models/custom_value.py
    :language: python
