# django-enum

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI version](https://badge.fury.io/py/django-enum.svg)](https://pypi.python.org/pypi/django-enum/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/django-enum.svg)](https://pypi.python.org/pypi/django-enum/)
[![PyPI djversions](https://img.shields.io/pypi/djversions/django-enum.svg)](https://pypi.org/project/django-enum/)
[![PyPI status](https://img.shields.io/pypi/status/django-enum.svg)](https://pypi.python.org/pypi/django-enum)
[![Documentation Status](https://readthedocs.org/projects/django-enum/badge/?version=latest)](http://django-enum.readthedocs.io/?badge=latest/)
[![Code Cov](https://codecov.io/gh/bckohan/django-enum/branch/main/graph/badge.svg?token=0IZOKN2DYL)](https://codecov.io/gh/bckohan/django-enum)
[![Test Status](https://github.com/bckohan/django-enum/workflows/test/badge.svg)](https://github.com/bckohan/django-enum/actions/workflows/test.yml)
[![Lint Status](https://github.com/bckohan/django-enum/workflows/lint/badge.svg)](https://github.com/bckohan/django-enum/actions/workflows/lint.yml)

---------------------------------------------------------------------------------------------------

[![Postgres](https://img.shields.io/badge/Postgres-9.6%2B-blue)](https://www.postgresql.org/)
[![MySQL](https://img.shields.io/badge/MySQL-5.7%2B-blue)](https://www.mysql.com/)
[![MariaDB](https://img.shields.io/badge/MariaDB-10.2%2B-blue)](https://mariadb.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3.8%2B-blue)](https://www.sqlite.org/)
[![Oracle](https://img.shields.io/badge/Oracle-18%2B-blue)](https://www.oracle.com/database/)

---------------------------------------------------------------------------------------------------

Full and natural support for [enumerations](https://docs.python.org/3/library/enum.html#enum.Enum) as Django model fields.

Many packages aim to ease usage of Python enumerations as model fields. Most were made obsolete when Django provided ``TextChoices`` and ``IntegerChoices`` types. The motivation for [django-enum](https://django-enum.readthedocs.io) was to:

* Work with any Python PEP 435 Enum including those that do not derive from Django's TextChoices and IntegerChoices.
* Always automatically coerce fields to instances of the Enum type.
* Allow strict adherence to Enum values to be disabled.
* Handle migrations appropriately. (See [migrations](https://django-enum.readthedocs.io/en/latest/usage.html#migrations))
* Integrate as fully as possible with [Django's](https://www.djangoproject.com) existing level of enum support.
* Support [enum-properties](https://pypi.org/project/enum-properties) and dataclass enumerations to enable richer enumeration types.
* Represent enum fields with the smallest possible column type.
* Provide bit mask functionality using standard Python Flag enumerations.
* Be as simple and light-weight an extension to core [Django](https://www.djangoproject.com) as possible.
* Optionally enforce enumeration value consistency at the database level using check constraints.

[django-enum](https://django-enum.readthedocs.io) works in concert with [Django's](https://www.djangoproject.com) built in ``TextChoices`` and ``IntegerChoices`` to provide a new model field type, ``EnumField``, that resolves the correct native [Django](https://www.djangoproject.com) field type for the given enumeration based on its value type and range. For example, ``IntegerChoices`` that contain values between 0 and 32767 become [PositiveSmallIntegerField](https://docs.djangoproject.com/en/stable/ref/models/fields/#positivesmallintegerfield).

```python

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
```

``EnumField`` **is more than just an alias. The fields are now assignable and accessible as their enumeration type rather than by-value:**

```python

    instance = MyModel.objects.create(
        txt_enum=MyModel.TextEnum.VALUE1,
        int_enum=3  # by-value assignment also works
    )

    assert instance.txt_enum == MyModel.TextEnum('V1')
    assert instance.txt_enum.label == 'Value 1'

    assert instance.int_enum == MyModel.IntEnum['THREE']
    assert instance.int_enum.value == 3
```

[django-enum](https://django-enum.readthedocs.io) also provides ``IntegerChoices`` and ``TextChoices`` types that extend from [enum-properties](https://pypi.org/project/enum-properties) which makes possible very rich enumeration fields.

``?> pip install enum-properties``

```python

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
```

Consider using [django-render-static](https://pypi.org/project/django-render-static) to make your enumerations [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) across the full stack!

Please report bugs and discuss features on the [issues page](https://github.com/bckohan/django-enum/issues).

[Contributions](https://github.com/bckohan/django-enum/blob/main/CONTRIBUTING.md) are encouraged!

[Full documentation at read the docs.](https://django-enum.readthedocs.io)

## Installation

1. Clone django-enum from GitHub_ or install a release off [pypi](https://pypi.org/project/django-enum):

```bash
   pip install django-enum
```

``django-enum`` has several optional dependencies that are not pulled in by default. ``EnumFields`` work seamlessly with all Django apps that work with model fields with choices without any additional work. Optional integrations are provided with several popular libraries to extend this basic functionality.

Integrations are provided that leverage [enum-properties](https://pypi.org/project/enum-properties) to make enumerations do more work and to provide extended functionality for [django-filter](https://pypi.org/project/django-filter) and [djangorestframework](https://www.django-rest-framework.org).

```bash
    pip install enum-properties
    pip install django-filter
    pip install djangorestframework
```

## Continuous Integration

Like with Django, Postgres is the preferred database for support. The full test suite is run against all combinations of currently supported versions of Django, Python, and Postgres as well as psycopg3 and psycopg2. The other RDBMS supported by Django are also tested including SQLite, MySQL, MariaDB and Oracle. For these RDBMS (with the exception of Oracle), tests are run against the minimum and maximum supported version combinations to maximize coverage breadth.

**See the [latest test runs](https://github.com/bckohan/django-enum/actions/workflows/test.yml) for our current test matrix**

*For Oracle, only the latest version of the free database is tested against the minimum and maximum supported versions of Python, Django and the cx-Oracle driver.*
