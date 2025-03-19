.. include:: ../refs.rst

.. _migrations:

================
Write Migrations
================

.. important::

    There is one rule for writing custom migration files for EnumFields:
    *Never reference or import your enumeration classes in a migration file,
    work with the primitive values instead*.

The deconstructed :class:`~django_enum.fields.EnumField` only include the choices tuple in the
migration files. This is because :class:`enum.Enum` classes may come and go or be
altered but the earlier migration files must still work. Simply treat any
custom migration routines as if they were operating on a normal model field
with choices.

:class:`~django_enum.fields.EnumField` in migration files will not resolve the field values to
enumeration types. The fields will be the primitive enumeration values as they
are with any field with choices.
