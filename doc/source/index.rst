.. include:: refs.rst

===========
Django Enum
===========

Full and natural support for enumerations_ as Django model fields.

`django-enum <https://django-enum.readthedocs.io/en/latest/>`_ provides a new
model field type, ``EnumField``, that resolves the correct native Django_ field
type for the given enumeration based on its value type and range. For example,
``IntegerChoices`` that contain values between 0 and 32767 become
`PositiveSmallIntegerField <https://docs.djangoproject.com/en/stable/ref/models/fields/#positivesmallintegerfield>`_.

.. code:: python

    from django.db import models
    from django_enum import EnumField

    class MyModel(models.Model):

        class TextEnum(models.TextChoices):

            VALUE0 = 'V0', 'Value 0'
            VALUE1 = 'V1', 'Value 1'
            VALUE2 = 'V2', 'Value 2'

        class IntEnum(models.IntegerChoices):

            ONE   = 1, 'One'
            TWO   = 2, 'Two',
            THREE = 3, 'Three'

        # this is equivalent to:
        #  CharField(max_length=2, choices=TextEnum.choices, null=True, blank=True)
        txt_enum = EnumField(TextEnum, null=True, blank=True)

        # this is equivalent to
        #  PositiveSmallIntegerField(choices=IntEnum.choices)
        int_enum = EnumField(IntEnum)


``EnumField`` *is more than just an alias. The fields are now assignable and
accessible as their enumeration type rather than by-value:*

.. code:: python

    instance = MyModel.objects.create(
        txt_enum=MyModel.TextEnum.VALUE1,
        int_enum=3  # by-value assignment also works
    )
    instance.refresh_from_db()

    assert instance.txt_enum == MyModel.TextEnum('V1')
    assert instance.txt_enum.label == 'Value 1'

    assert instance.int_enum == MyModel.IntEnum['THREE']
    assert instance.int_enum.value == 3


`django-enum <https://django-enum.readthedocs.io/en/latest/>`_ also provides
``IntegerChoices`` and ``TextChoices`` types that extend from
enum-properties_ which makes possible very rich enumeration fields.

.. code:: python

    from enum_properties import s
    from django_enum import TextChoices  # use instead of Django's TextChoices
    from django.db import models

    class MyModel(models.Model):

        class Color(TextChoices, s('rgb'), s('hex', case_fold=True)):

            # name   value   label       rgb       hex
            RED     = 'R',   'Red',   (1, 0, 0), 'ff0000'
            GREEN   = 'G',   'Green', (0, 1, 0), '00ff00'
            BLUE    = 'B',   'Blue',  (0, 0, 1), '0000ff'

            # any named s() values in the Enum's inheritance become properties on
            # each value, and the enumeration value may be instantiated from the
            # property's value

        color = EnumField(Color)

    instance = MyModel.objects.create(color=MyModel.Color('FF0000'))

    assert instance.color == TextChoicesExample.Color('Red')
    assert instance.color == TextChoicesExample.Color('R')
    assert instance.color == TextChoicesExample.Color((1, 0, 0))

    # save by any symmetric value or enum type instance
    instance.color = 'FF0000'
    instance.full_clean()
    assert instance.color.hex == 'ff0000'
    instance.save()

    # filtering works by any symmetric value or enum type instance
    assert TextChoicesExample.objects.filter(
        color=TextChoicesExample.Color.RED
    ).first() == instance

    assert TextChoicesExample.objects.filter(color=(1, 0, 0)).first() == instance

    assert TextChoicesExample.objects.filter(color='FF0000').first() == instance

.. note::

    Consider using
    `django-render-static <https://pypi.org/project/django-render-static/>`_
    to make your enumerations DRY_ across the full stack!

Please report bugs and discuss features on the
`issues page <https://github.com/bckohan/django-enum/issues>`_.

`Contributions <https://github.com/bckohan/django-enum/blob/main/CONTRIBUTING.rst>`_
are encouraged!

`Full documentation at read the docs. <https://django-enum.readthedocs.io/en/latest/>`_

Installation
------------

1. Clone django-enum from GitHub_ or install a release off PyPI_ :

.. code:: bash

       pip install django-enum

.. note::

    ``django-enum`` *does not* need to be added to ``INSTALLED_APPS``.

.. note::

    ``django-enum`` has several optional dependencies that are not pulled in
    by default. To utilize the
    enum-properties_ choice types you must `pip install enum-properties` and
    to use the ``EnumFilter`` type for django-filter_ you must
    `pip install django-filter`.

If features are utilized that require a missing optional dependency an
exception will be thrown.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage
   examples
   reference
   changelog
