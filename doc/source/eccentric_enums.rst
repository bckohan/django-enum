.. include:: refs.rst

.. _eccentric:

======================
Eccentric Enumerations
======================

Python's Enum_ type is extremely lenient. Enumeration values may be any
hashable type and values of the same enumeration may be of different types.

For use in databases it is recommended to use more strict enumeration types
that only allow a single value type of either string or integer. If additional
properties need to be associated with enumeration values, a library like
enum-properties_ should be used to store them on the enumeration value classes.

However, the goal of django-enum is to provide as complete a bridge as possible
between Python and the database so eccentric enumerations are supported with
caveats. The following enumeration value types are supported out of the box,
and map to the obvious Django model field type:

* :class:`int`
* :class:`str`
* :class:`float`
* :class:`datetime.date`
* :class:`datetime.datetime`
* :class:`datetime.time`
* :class:`datetime.timedelta`
* :class:`decimal.Decimal`

While it is mostly not advisable to use eccentric enumerations, there may be
some compelling reasons to do so. For example, it may make sense in
situations where the database will be used in a non-Python context and the
enumeration values need to retain their native meaning.


Mixed Value Enumerations
========================

Mixed value enumerations are supported. For example:

.. code-block:: python

    from enum import Enum

    class EccentricEnum(Enum):

        NONE = None
        VAL1 = 1
        VAL2 = '2.0'
        VAL3 = 3.0
        VAL4 = Decimal('4.5')


:class:`~django_enum.fields.EnumField` will determine the most appropriate database column type
to store the enumeration by trying each of the supported primitive types in order and
selecting the first one that is symmetrically coercible to and from each
enumeration value. ``None`` values are allowed and do not take part in the
primitive type selection. In the above example, the database column type would
be a string.

.. note::

    If none of the supported primitive types are symmetrically coercible
    :class:`~django_enum.fields.EnumField` will not be able to determine an appropriate column
    type and a ``ValueError`` will be raised.

In these cases, or to override the primitive type selection made by
:class:`~django_enum.fields.EnumField`, pass the ``primitive`` parameter. It may be necessary to
extend one of the supported primitives to make it coercible. It may also be necessary
to override the Enum_'s ``_missing_`` method:

.. code-block:: python

    # eccentric will be a string
    eccentric_str = EnumField(EccentricEnum)

    # primitive will be a float
    eccentric_float = EnumField(EccentricEnum, primitive=float)

In the above case since ``None`` is an enumeration value, :class:`~django_enum.fields.EnumField`
will automatically set null=True on the model field.

Custom Enumeration Values
=========================

.. warning::
    There is almost certainly a better way to do what you might be trying to do
    by writing a custom enumeration value - for example consider using
    enum-properties_ to make your enumeration types more robust by pushing more
    of this functionality on the Enum_ class itself.

If you must use a custom value type, you can by specifying a symmetrically
coercible primitive type. For example Path is already symmetrically coercible
to str so this works:

.. code-block:: python

    class MyModel(models.Model):

        class PathEnum(Enum):

            USR = Path('/usr')
            USR_LOCAL = Path('/usr/local')
            USR_LOCAL_BIN = Path('/usr/local/bin')

        path = EnumField(PathEnum, primitive=str)


A fully custom value might look like the following (admittedly contrived)
example:

.. code-block:: python

    class StrProps:
        """
        Wrap a string with some properties.
        """

        _str = ''

        def __init__(self, string):
            self._str = string

        def __str__(self):
            """ coercion to str - str(StrProps('str1')) == 'str1' """
            return self._str

        @property
        def upper(self):
            return self._str.upper()

        @property
        def lower(self):
            return self._str.lower()

        def __eq__(self, other):
            """ Make sure StrProps('str1') == 'str1' """
            if isinstance(other, str):
                return self._str == other
            if other is not None:
                return self._str == other._str
            return False

        def deconstruct(self):
            """Necessary to construct choices and default in migration files"""
            return 'my_module.StrProps', (self._str,), {}


    class MyModel(models.Model):

        class StrPropsEnum(Enum):

            STR1 = StrProps('str1')
            STR2 = StrProps('str2')
            STR3 = StrProps('str3')

        str_props = EnumField(StrPropsEnum, primitive=str)

