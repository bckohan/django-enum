|MIT license| |PyPI version fury.io| |PyPI pyversions| |PyPI status| |Documentation Status|
|Code Cov| |Test Status|

.. |MIT license| image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://lbesson.mit-license.org/

.. |PyPI version fury.io| image:: https://badge.fury.io/py/django-enum.svg
   :target: https://pypi.python.org/pypi/django-enum/

.. |PyPI pyversions| image:: https://img.shields.io/pypi/pyversions/django-enum.svg
   :target: https://pypi.python.org/pypi/django-enum/

.. |PyPI status| image:: https://img.shields.io/pypi/status/django-enum.svg
   :target: https://pypi.python.org/pypi/django-enum

.. |Documentation Status| image:: https://readthedocs.org/projects/django-enum/badge/?version=latest
   :target: http://django-enum.readthedocs.io/?badge=latest/

.. |Code Cov| image:: https://codecov.io/gh/bckohan/django-enum/branch/main/graph/badge.svg?token=0IZOKN2DYL
   :target: https://codecov.io/gh/bckohan/django-enum

.. |Test Status| image:: https://github.com/bckohan/django-enum/workflows/test/badge.svg
   :target: https://github.com/bckohan/django-enum/actions


.. _Django: https://www.djangoproject.com/
.. _GitHub: https://github.com/bckohan/django-enum
.. _PyPI: https://pypi.python.org/pypi/django-enum
.. _Enum: https://docs.python.org/3/library/enum.html#enum.Enum
.. _enumerations: https://docs.python.org/3/library/enum.html#enum.Enum
.. _ValueError: https://docs.python.org/3/library/exceptions.html#ValueError
.. _DRY: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself

Django Enum
###########

Full and natural support for enumerations_ as Django model fields.

Many packages aim to ease usage of Python enumerations as model fields. Most
were made obsolete when Django provided ``TextChoices`` and ``IntegerChoices``
types. The motivation for `django-enum <https://django-enum.readthedocs.io/en/latest/>`_
was to:

* Always automatically coerce fields to instances of the Enum type.
* Allow strict adherence to Enum values to be disabled.
* Handle migrations appropriately. (See `migrations <https://django-enum.readthedocs.io/en/latest/usage.html#migrations>`_)
* Integrate as fully as possible with Django_'s existing level of enum support.
* Integrate with `enum-properties <https://pypi.org/project/enum-properties/>`_ to enable richer enumeration types.
* Represent enum fields with the smallest possible column type.
* Be as simple and light-weight an extension to core Django as possible.

`django-enum <https://django-enum.readthedocs.io/en/latest/>`_ works in concert
with Django_'s built in ``TextChoices`` and ``IntegerChoices`` to provide a
new model field type, ``EnumField``, that resolves the correct native Django_
field type for the given enumeration based on its value type and range. For
example, ``IntegerChoices`` that contain values between 0 and 32767 become
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


``EnumField`` **is more than just an alias. The fields are now assignable and
accessible as their enumeration type rather than by-value:**

.. code:: python

    instance = MyModel.objects.create(
        txt_enum=MyModel.TextEnum.VALUE1,
        int_enum=3  # by-value assignment also works
    )

    assert instance.txt_enum == MyModel.TextEnum('V1')
    assert instance.txt_enum.label == 'Value 1'

    assert instance.int_enum == MyModel.IntEnum['THREE']
    assert instance.int_enum.value == 3


`django-enum <https://django-enum.readthedocs.io/en/latest/>`_ also provides
``IntegerChoices`` and ``TextChoices`` types that extend from
`enum-properties <https://pypi.org/project/enum-properties/>`_ which makes
possible very rich enumeration fields.

.. code:: python

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

    # access any enum property right from the model field
    assert instance.color.hex == 'ff0000'

    # this also works!
    assert instance.color == 'ff0000'

    # and so does this!
    assert instance.color == 'FF0000'

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

    ``django-enum`` has several optional dependencies that are not pulled in
    by default. ``EnumFields`` work seamlessly with all Django apps that
    work with model fields with choices without any additional work. Optional
    integrations are provided with several popular libraries to extend this
    basic functionality.

Integrations are provided that leverage
`enum-properties <https://pypi.org/project/enum-properties/>`_ to make
enumerations do more work and to provide extended functionality for
`django-filter <https://pypi.org/project/django-filter/>`_  and
`djangorestframework <https://www.django-rest-framework.org>`_.

.. code:: bash

    pip install enum-properties
    pip install django-filter
    pip install djangorestframework

If features are utilized that require a missing optional dependency an
exception will be thrown.
