.. include:: ../refs.rst

.. _flag_enums:

=====================
Use Flags (BitFields)
=====================

Python supports `bit fields <https://en.wikipedia.org/wiki/Bit_field>`_ through the
:class:`enum.Flag` extension to :class:`enum.Enum`.

These enumerations are fully supported and will render as multi select form fields by default. For
example:

.. _group_permissions_ex:

.. literalinclude:: ../../../tests/examples/models/flag_howto.py
    :lines: 2-

.. literalinclude:: ../../../tests/examples/flag_howto.py
    :lines: 14-22

**Two new field lookups are provided for flag enumerations:** :ref:`has_any` **and** :ref:`has_all`.

.. _has_any:

has_any
-------

The :ref:`has_any` lookup will return any object that has at least one of the flags in the
referenced enumeration. For example:

.. literalinclude:: ../../../tests/examples/flag_howto.py
    :lines: 23-30

.. _has_all:

has_all
-------

The :ref:`has_all` lookup will return any object that has at least all of the flags in the
referenced enumeration. For example:

.. literalinclude:: ../../../tests/examples/flag_howto.py
    :lines: 32-

**There are performance considerations when using a bit mask like a Flag enumeration instead of
multiple boolean columns.** See :ref:`flag performance <flag_performance>` for discussion and
benchmarks.

.. _large_flags:

Flags with more than 64 bits
----------------------------

Flag enumerations of arbitrary size are supported, however if the enum has more than 64 flags it
will be stored as a :class:`~django.db.models.BinaryField`. It is therefore strongly recommended to
keep your :class:`enum.IntFlag` enumerations at 64 bits or less.

.. warning::

    Support for extra large flag fields is experimental. :ref:`has_any` and :ref:`has_all` do not
    work. Most RDBMS systems do not support bitwise operations on binary fields. Future work may
    involve exploring support for this as a Postgres extension.
