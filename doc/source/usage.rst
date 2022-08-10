.. include:: refs.rst

=====
Usage
=====


Parameters
##########

All parameters available to the equivalent model field with choices may be set
directly in the ``EnumField`` instantiation. If not provided EnumField will set
``choices`` and ``max_length`` automatically.

The following ``EnumField`` specific parameters are available:

``strict``
----------

By default all ``EnumFields`` are ``strict``. This means a ``ValidationError``
will be thrown anytime full_clean is run on a model and a value is set for the
field that can not be coerced to its native ``Enum`` type. To allow the field
to store values that are not present in the fields ``Enum`` type we can pass
`strict=False`.

Non-strict fields that have values outside of the enumeration will be instances
of the enumeration where a valid ``Enum`` value is present and the plain old
data where no ``Enum`` type coercion is possible.

.. code-block:: python

    class StrictExample(models.Model):

        class EnumType(TextChoices):

            ONE = '1', 'One'
            TWO = '2', 'Two'

        non_strict = EnumField(
            EnumType,
            strict=False,
            # it might be necessary to override max_length also, otherwise
            # max_length will be 1
            max_length=10
        )

    obj = StrictExample()

    # set to a valid EnumType value
    obj.non_strict = '1'
    obj.full_clean()
    # when accessed from the db or after clean, will be an EnumType instance
    assert obj.non_strict is StrictExample.EnumType.ONE

    # we can also store any string less than or equal to length 10
    obj.non_strict = 'arbitrary'
    obj.full_clean()  # no errors
    # when accessed will be a str instance
    assert obj.non_strict == 'arbitrary'


``coerce``
----------

Setting this parameter to ``False`` will turn off the automatic conversion to
the field's ``Enum`` type while leaving all validation checks in place. It will
still be possible to set the field directly as an ``Enum`` instance and to
filter by ``Enum`` instance or any symmetric value:

.. code-block:: python

    non_strict = EnumField(
        EnumType,
        strict=False,
        coerce=False,
        # it might be necessary to override max_length also, otherwise
        # max_length will be 1
        max_length=10
    )

    # set to a valid EnumType value
    obj.non_strict = '1'
    obj.full_clean()

    # when accessed from the db or after clean, will be the primitive value
    assert obj.non_strict == '1'
    assert isinstance(obj.non_strict, str)
    assert not isinstance(obj.non_strict, StrictExample.EnumType)


enum-properties
###############

``TextChoices`` and ``IntegerChoices`` types are provided that extend Django_'s
native choice types with support for enum-properties_. The dependency on
enum-properties_ is optional, so to utilize these classes you must separately
install enum-properties_:

.. code:: bash

       pip install enum-properties

These choice extensions make possible very rich enumerations that have other
values that can be symmetrically mapped back to enumeration values:

.. code-block::

    from enum_properties import s
    from django_enum import TextChoices  # use instead of Django's TextChoices
    from django.db import models

    class TextChoicesExample(models.Model):

        class Color(TextChoices, s('rgb'), s('hex', case_fold=True)):

            # name   value   label       rgb       hex
            RED     = 'R',   'Red',   (1, 0, 0), 'ff0000'
            GREEN   = 'G',   'Green', (0, 1, 0), '00ff00'
            BLUE    = 'B',   'Blue',  (0, 0, 1), '0000ff'

            # any named s() values in the Enum's inheritance become properties on
            # each value, and the enumeration value may be instantiated from the
            # property's value

        color = EnumField(Color)

    instance = TextChoicesExample.objects.create(
        color=TextChoicesExample.Color('FF0000')
    )
    assert instance.color == TextChoicesExample.Color('Red')
    assert instance.color == TextChoicesExample.Color('R')
    assert instance.color == TextChoicesExample.Color((1, 0, 0))

    # direct comparison to any symmetric value also works
    assert instance.color == 'Red'
    assert instance.color == 'R'
    assert instance.color == (1, 0, 0)

    # save by any symmetric value
    instance.color = 'FF0000'
    instance.full_clean()
    assert instance.color.hex == 'ff0000'
    instance.save()

For a real-world example see :ref:`examples`.

Forms
#####

EnumFields will behave as normal model fields with choices when used in
Django_'s ModelForms. To enable


Filtering
#########



Migrations
##########

.. important::

    There is one rule for writing custom migration files for EnumFields:
    *Never reference or import your enumeration classes in a migration file,
    work with the primitive values instead*.

The deconstructed ``EnumFields`` only include the choices tuple in the
migration files. This is because ``Enum`` classes may come and go or be
altered but the earlier migration files must still work. Simply treat any
custom migration routines as if they were operating on a normal model field
with choices.

``EnumFields`` in migration files will not resolve the field values to
enumeration types. The fields will be the primitive enumeration values as they
are with any field with choices.

Performance
###########

The cost to resolve a raw database value into an ``Enum`` type object is
non-zero. ``EnumFields`` may not be appropriate for use cases at the edge of
critical performance boundaries, but for most scenarios the cost of using
``EnumFields`` is negligible.

An effort is made to characterize and monitor the performance penalty of
using ``EnumFields`` over a Django_ native field with choices and integration
tests assure performance of future releases will not worsen.

.. note::

    The read performance penalty can be eliminated by setting ``coerce`` to
    ``False``.
