.. include:: refs.rst

===========
Django Enum
===========

|MIT license| |Ruff| |PyPI version fury.io| |PyPI pyversions| |PyPi djversions| |PyPI status|
|Documentation Status| |Code Cov| |Test Status|


|Postgres| |MySQL| |MariaDB| |SQLite| |Oracle|

.. |MIT license| image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://lbesson.mit-license.org/

.. |Ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
   :target: https://docs.astral.sh/ruff

.. |PyPI version fury.io| image:: https://badge.fury.io/py/django-enum.svg
   :target: https://pypi.python.org/pypi/django-enum/

.. |PyPI pyversions| image:: https://img.shields.io/pypi/pyversions/django-enum.svg
   :target: https://pypi.python.org/pypi/django-enum/

.. |PyPI djversions| image:: https://img.shields.io/pypi/djversions/django-enum.svg
   :target: https://pypi.org/project/django-enum/

.. |PyPI status| image:: https://img.shields.io/pypi/status/django-enum.svg
   :target: https://pypi.python.org/pypi/django-enum

.. |Documentation Status| image:: https://readthedocs.org/projects/django-enum/badge/?version=latest
   :target: http://django-enum.readthedocs.io/?badge=latest/

.. |Code Cov| image:: https://codecov.io/gh/bckohan/django-enum/branch/main/graph/badge.svg?token=0IZOKN2DYL
   :target: https://codecov.io/gh/bckohan/django-enum

.. |Test Status| image:: https://github.com/bckohan/django-enum/workflows/test/badge.svg
   :target: https://github.com/bckohan/django-enum/actions/workflows/test.yml

.. |Lint Status| image:: https://github.com/bckohan/django-enum/workflows/lint/badge.svg
   :target: https://github.com/bckohan/django-enum/actions/workflows/lint.yml

.. |Postgres| image:: https://img.shields.io/badge/Postgres-9.6%2B-blue
   :target: https://www.postgresql.org/

.. |MySQL| image:: https://img.shields.io/badge/MySQL-5.7%2B-blue
    :target: https://www.mysql.com

.. |MariaDB| image:: https://img.shields.io/badge/MariaDB-10.2%2B-blue
    :target: https://mariadb.org/

.. |SQLite| image:: https://img.shields.io/badge/SQLite-3.8%2B-blue
    :target: https://www.sqlite.org/

.. |Oracle| image:: https://img.shields.io/badge/Oracle-18%2B-blue
    :target: https://www.oracle.com/database/

----

.. tip::

    See :ref:`migration_1.x_to_2.x` for how to update from 1.x to 2.x.

Full and natural support for enumerations_ as Django_ model fields.

Many packages aim to ease usage of Python enumerations as model fields. Most were superseded when
Django provided ``TextChoices`` and ``IntegerChoices`` types. The motivation for django-enum_ was
to:

* Work with any Python PEP 435 Enum including those that do not derive from Django's
  ``TextChoices`` and ``IntegerChoices``.
* Coerce fields to instances of the Enum type by default.
* Allow strict adherence to Enum values to be disabled.
* Handle migrations appropriately. (See :ref:`migrations`)
* Integrate as fully as possible with Django's existing level of enum support.
* Support enum-properties_ to enable richer enumeration types. (A less awkward alternative to
  dataclass enumerations with more features)
* Represent enum fields with the smallest possible column type.
* Support bit mask queries using standard Python Flag enumerations.
* Be as simple and light-weight an extension to core Django_ as possible.
* Enforce enumeration value consistency at the database level using check constraints by default.
* (TODO) Support native database enumeration column types when available.

django-enum_ provides a new model field type, :class:`~django_enum.fields.EnumField`, that allows
you to treat almost any PEP 435 enumeration as a database column.
:class:`~django_enum.fields.EnumField` resolves the correct native Django_ field type for the given
enumeration based on its value type and range. For example, ``IntegerChoices`` that contain values
between 0 and 32767 become `PositiveSmallIntegerField <https://docs.djangoproject.com/en/stable/ref/models/fields/#positivesmallintegerfield>`_.

.. code-block:: python

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
        #  PositiveSmallIntegerField(choices=IntEnum.choices, default=IntEnum.ONE.value)
        int_enum = EnumField(IntEnum, default=IntEnum.ONE)


:class:`~django_enum.fields.EnumField` **is more than just an alias. The fields are now assignable
and accessible as their enumeration type rather than by-value:**

.. code-block:: python

    instance = MyModel.objects.create(
        txt_enum=MyModel.TextEnum.VALUE1,
        int_enum=3  # by-value assignment also works
    )

    assert instance.txt_enum is MyModel.TextEnum('V1')
    assert instance.txt_enum.label is 'Value 1'

    assert instance.int_enum is MyModel.IntEnum['THREE']
    assert instance.int_enum.value is 3


Flag Support
============

Flag_ types are also seamlessly supported! This allows a database column to behave like a bit mask
and is an alternative to multiple boolean columns. There are mostly positive performance
implications for using a bit mask instead of booleans depending on the size of the bit mask and the
types of queries you will run against it. For bit masks more than a few bits long the size
reduction both speeds up queries and reduces the required storage space. See the documentation for
:ref:`discussion and benchmarks <flag_performance>`.

.. code-block:: python

    class Permissions(IntFlag):

        READ = 1**2
        WRITE = 2**2
        EXECUTE = 3**2


    class FlagExample(models.Model):

        permissions = EnumField(Permissions)


    FlagExample.objects.create(permissions=Permissions.READ | Permissions.WRITE)

    # get all models with RW:
    FlagExample.objects.filter(permissions__has_all=Permissions.READ | Permissions.WRITE)

.. note::

    The :ref:`has_all` and :ref:`has_any` field lookups are only available for Flag enumerations.

Complex Enumerations
====================

django-enum_ supports enum types that do not derive from Django's ``IntegerChoices`` and
``TextChoices``. This allows us to use other libs like enum-properties_ which makes possible very
rich enumeration fields:

.. code-block:: console

    ?> pip install enum-properties

.. code-block:: python

    from enum_properties import StrEnumProperties
    from django.db import models

    class TextChoicesExample(models.Model):

        class Color(StrEnumProperties):

            label: Annotated[str, Symmetric()]
            rgb: Annotated[t.Tuple[int, int, int], Symmetric()]
            hex: Annotated[str, Symmetric(case_fold=True)]

            # name value label       rgb       hex
            RED   = "R", "Red",   (1, 0, 0), "ff0000"
            GREEN = "G", "Green", (0, 1, 0), "00ff00"
            BLUE  = "B", "Blue",  (0, 0, 1), "0000ff"

            # any named s() values in the Enum's inheritance become properties on
            # each value, and the enumeration value may be instantiated from the
            # property's value

        color = EnumField(Color)

    instance = TextChoicesExample.objects.create(
        color=TextChoicesExample.Color('FF0000')
    )
    assert instance.color is TextChoicesExample.Color('Red')
    assert instance.color is TextChoicesExample.Color('R')
    assert instance.color is TextChoicesExample.Color((1, 0, 0))

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


While they should be unnecessary if you need to integrate with code that expects an interface fully
compatible with Django's ``TextChoices`` and ``IntegerChoices`` django-enum_ provides
``TextChoices``, ``IntegerChoices``, ``FlagChoices`` and ``FloatChoices`` types that derive from
enum-properties_ and Django's ``Choices``. So the above enumeration could also be written:

.. code-block:: python

    from django_enum.choices import TextChoices

    class Color(TextChoices):

        # label is added as a symmetric property by the base class

        rgb: Annotated[t.Tuple[int, int, int], Symmetric()]
        hex: Annotated[str, Symmetric(case_fold=True)]

        # name value label       rgb       hex
        RED   = "R", "Red",   (1, 0, 0), "ff0000"
        GREEN = "G", "Green", (0, 1, 0), "00ff00"
        BLUE  = "B", "Blue",  (0, 0, 1), "0000ff"


Installation
============

1. Clone django-enum from GitHub_ or install a release off PyPI_:

.. code-block:: console

   ?> pip install django-enum


django-enum_ has several optional dependencies that are not pulled in by default. ``EnumFields``
work seamlessly with all Django apps that work with model fields with choices without any
additional work. Optional integrations are provided with several popular libraries to extend this
basic functionality.

Integrations are provided that leverage enum-properties_ to make enumerations do more work and to
provide extended functionality for django-filter_ and djangorestframework_.

.. code-block:: console

    ?> pip install enum-properties
    ?> pip install django-filter
    ?> pip install djangorestframework


Continuous Integration
======================

Like with Django, Postgres is the preferred database for support. The full test suite is run
against all combinations of currently supported versions of Django, Python, and Postgres as well as
psycopg3 and psycopg2. The other RDBMS supported by Django are also tested including SQLite, MySQL,
MariaDB and Oracle. For these RDBMS (with the exception of Oracle), tests are run against the
minimum and maximum supported version combinations to maximize coverage breadth.

**See the** `latest test runs <https://github.com/bckohan/django-enum/actions/workflows/test.yml>`_
**for our current test matrix**

*For Oracle, only the latest version of the free database is tested against the minimum and
maximum supported versions of Python, Django and the cx-Oracle driver.*

Further Reading
===============

Consider using django-render-static_ to make your enumerations DRY_ across the full stack!

Please report bugs and discuss features on the
`issues page <https://github.com/bckohan/django-enum/issues>`_.

`Contributions <https://github.com/bckohan/django-enum/blob/main/CONTRIBUTING.md>`_ are encouraged!


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage
   examples
   performance
   eccentric_enums
   reference
   changelog
