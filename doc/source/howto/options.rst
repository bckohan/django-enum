.. include:: ../refs.rst

.. _options:

====================
Configure EnumFields
====================

All parameters available to the equivalent model field with choices may be set directly in the
:class:`~django_enum.fields.EnumField` instantiation. If not provided
:class:`~django_enum.fields.EnumField` will set ``choices`` and ``max_length`` automatically.

The following :class:`~django_enum.fields.EnumField` specific parameters are available:

``strict``
----------

By default all :class:`~django_enum.fields.EnumField` are ``strict``. This means a
:exc:`~django.core.exceptions.ValidationError` will be thrown anytime
:meth:`~django.db.models.Model.full_clean` is run on a model and a value is set for the field that
can not be coerced to its native :class:`~enum.Enum` type. To allow the field to store values that
are not present in the fields :class:`~enum.Enum` type we can pass `strict=False`.

Non-strict fields will be instances of the enumeration where a valid :class:`~enum.Enum` value is
present and the plain old data where no :class:`~enum.Enum` type coercion is possible.

.. literalinclude:: ../../../tests/examples/models/strict.py

.. literalinclude:: ../../../tests/examples/strict_howto.py
    :lines: 4-


``constrained``
---------------

By default all strict :class:`~django_enum.fields.EnumField` are ``constrained``. This means that
:doc:`CheckConstraints <django:ref/models/constraints>` will be generated at the database level
to ensure that the column will reject any value that is not present in the enumeration. This is a
good idea for most use cases, but it can be turned off by setting ``constrained`` to ``False``.

.. note::

    This is new in version 2.0. If you are upgrading from a previous version, you may set
    this parameter to ``False`` to maintain the previous behavior.

``primitive``
-------------

:class:`~django_enum.fields.EnumField` dynamically determines the database column type by
determining the most appropriate primitive type for the enumeration based on the enumeration
values. You may override the primitive determined by :class:`~django_enum.fields.EnumField` by
passing a type to the ``primitive`` parameter. You will likely not need to do this unless your
enumeration is :ref:`eccentric <eccentric>` in some way.

``coerce``
----------

Setting this parameter to ``False`` will turn off the automatic conversion to
the field's :class:`~enum.Enum` type while leaving all validation checks in place. It will
still be possible to set the field directly as an :class:`~enum.Enum` instance and to
filter by :class:`~enum.Enum` instance or any symmetric value:

.. literalinclude:: ../../../tests/examples/models/no_coerce.py
    :lines: 13-

.. literalinclude:: ../../../tests/examples/no_coerce_howto.py
    :lines: 6-
