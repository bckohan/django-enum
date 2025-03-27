.. include:: ../refs.rst

.. _migrations:

================
Write Migrations
================

.. important::

    There is one rule for writing custom migration files for EnumFields:
    **Never reference or import your enumeration classes in a migration file,
    work with the primitive values instead**. If your :class:`~enum.Enum` class
    changes over time, this can break older migration files. Always working with
    primitive values in migrations files will ensure that the migration will be
    valid to the data as it existed when the migration was generated.

The deconstructed :class:`~django_enum.fields.EnumField` only include the choices tuple in the
migration files. This is because :class:`enum.Enum` classes may come and go or be
altered but the earlier migration files must still work. Simply treat any
custom migration routines as if they were operating on a normal model field
with choices.

:class:`~django_enum.fields.EnumField` in migration files will not resolve the field values to
enumeration types. The fields will be the primitive enumeration values as they
are with any field with choices.


Using :class:`enum.auto`
------------------------

If your :class:`~django_enum.fields.EnumField` is storing the value as the database column
(default) it is best to avoid the usage of :class:`enum.auto` because the value for each
enumerated instance may change which would bring your database out of sync with your
codebase.

If you have to use :class:`enum.auto` it is best to add integration tests to check for value
changes.
