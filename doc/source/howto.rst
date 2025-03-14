.. include:: refs.rst

======
How To
======

:class:`~django_enum.fields.EnumField` inherits from the appropriate native Django_ field and sets
the correct choice tuple set based on the enumeration type. This means
:class:`~django_enum.fields.EnumField` are compatible with all modules, utilities and libraries
that fields defined with a choice tuple are. For example:

.. code:: python

    from django.db import models
    from django_enum import EnumField

    class MyModel(models.Model):

        class TextEnum(models.TextChoices):

            VALUE0 = 'V0', 'Value 0'
            VALUE1 = 'V1', 'Value 1'
            VALUE2 = 'V2', 'Value 2'

        txt_enum = EnumField(TextEnum, null=True, blank=True, default=None)

        txt_choices = models.CharField(
            max_length=2,
            choices=MyModel.TextEnum.choices,
            null=True,
            blank=True,
            default=None
        )

``txt_enum`` and ``txt_choices`` fields are equivalent in all ways with the
following exceptions:

.. code:: python

    # txt_enum fields will always be an instance of the TextEnum type, unless
    # set to a value that is not part of the enumeration

    assert isinstance(MyModel.objects.first().txt_enum, MyModel.TextEnum)
    assert not isinstance(MyModel.objects.first().txt_choices, MyModel.TextEnum)

    # by default EnumFields are more strict, this is possible:
    MyModel.objects.create(txt_choices='AA')

    # but this will throw a ValueError (unless strict=False)
    MyModel.objects.create(txt_enum='AA')

    # and this will throw a ValidationError
    MyModel(txt_enum='AA').full_clean()

Any ``ModelForms``, DRF serializers and filters will behave the same way with
``txt_enum`` and ``txt_choices``. A few types are provided for deeper
integration with forms and django-filter_ but their usage is optional.
See :ref:`forms` and :ref:`filtering`.

Very rich enumeration fields that encapsulate much more functionality in a
simple declarative syntax are possible with :class:`~django_enum.fields.EnumField`. See
:ref:`enum_props`.


External Enum Types
###################

:class:`enum.Enum` classes defined externally to your code base or enum classes that otherwise do
not inherit from Django's :ref:`field-choices-enum-types`, are supported. When no choices are
present on an :class:`enum.Enum` type, :class:`~django_enum.fields.EnumField` will attempt to use
the ``label`` member on each enumeration value if it is present, otherwise the labels will be based
off the enumeration name. Choices can also be overridden at the
:class:`~django_enum.fields.EnumField` declaration.

In short, :class:`~django_enum.fields.EnumField` should work with any subclass of
:class:`enum.Enum`.

.. code:: python

    from enum import Enum
    from django.db import models
    from django_enum import EnumField

    class MyModel(models.Model):

        class TextEnum(str, Enum)

            VALUE0 = 'V0'
            VALUE1 = 'V1'
            VALUE2 = 'V2'

        txt_enum = EnumField(TextEnum)

The above code will produce a choices set like ``[('V0', 'VALUE0'), ...]``.

.. warning::

    One nice feature of Django's :ref:`field-choices-enum-types` are that they disable
    ``auto()`` on :class:`enum.Enum` fields. ``auto()`` can be dangerous because the
    values assigned depend on the order of declaration. This means that if the
    order changes existing database values will no longer align with the
    enumeration values. When using ``Enums`` where control over the values is
    not certain it is a good idea to add integration tests that look for value
    changes.


Parameters
##########

All parameters available to the equivalent model field with choices may be set directly in the
:class:`~django_enum.fields.EnumField` instantiation. If not provided
:class:`~django_enum.fields.EnumField` will set ``choices`` and ``max_length`` automatically.

The following :class:`~django_enum.fields.EnumField` specific parameters are available:

``strict``
----------

By default all :class:`~django_enum.fields.EnumField` are ``strict``. This means a
:exc:`~django.core.exceptions.ValidationError` will be thrown anytime
:meth:`django.db.models.Model.full_clean` is run on a model and a value is set for the
field that can not be coerced to its native :class:`enum.Enum` type. To allow the field
to store values that are not present in the fields :class:`enum.Enum` type we can pass
`strict=False`.

Non-strict fields that have values outside of the enumeration will be instances
of the enumeration where a valid :class:`enum.Enum` value is present and the plain old
data where no :class:`enum.Enum` type coercion is possible.

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
    # when accessed will be an EnumType instance
    assert obj.non_strict is StrictExample.EnumType.ONE

    # we can also store any string less than or equal to length 10
    obj.non_strict = 'arbitrary'
    obj.full_clean()  # no errors
    # when accessed will be a str instance
    assert obj.non_strict == 'arbitrary'

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
the field's :class:`enum.Enum` type while leaving all validation checks in place. It will
still be possible to set the field directly as an :class:`enum.Enum` instance and to
filter by :class:`enum.Enum` instance or any symmetric value:

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

    # when accessed will be the primitive value
    assert obj.non_strict == '1'
    assert isinstance(obj.non_strict, str)
    assert not isinstance(obj.non_strict, StrictExample.EnumType)


.. _enum_props:

enum-properties
###############

Almost any :class:`enum.Enum` type is supported, so you may make use of :class:`enum.Enum`
extension libraries like :doc:`enum-properties:index` to define very rich enumeration fields:

.. code:: bash

       pip install enum-properties

:doc:`enum-properties:index` is an extension to :class:`enum.Enum` that allows properties to be
added to enumeration instances using a simple declarative syntax. This is a less awkward and more
compatible alternative than dataclass enumerations.

If you find yourself considering a dataclass enumeration, consider using
:doc:`enum-properties:index` instead. dataclass enumerations do not work with
:class:`~django_enum.fields.EnumField` because their value type is a dataclass. Futher, most
libraries that expect to be able to work with enumerations expect the ``value`` attribute to be a
primitive serializable type.

.. code-block:: python

    import typing as t
    from enum_properties import StrEnumProperties, Symmetric
    from django_enum.choices import TextChoices  # use instead of Django's TextChoices
    from django.db import models

    class TextChoicesExample(models.Model):

        class Color(StrEnumProperties):

            label: t.Annotated[str, Symmetric()]
            rgb: t.Annotated[t.Tuple[int, int, int], Symmetric()]
            hex: t.Annotated[str, Symmetric(case_fold=True)]

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

For a real-world example see :ref:`examples`.

It should be unnecessary, but if you need to integrate with code that expects an interface fully
compatible with Django's
`enumeration types <https://docs.djangoproject.com/en/stable/ref/models/fields/#enumeration-types>`_
(``TextChoices`` and ``IntegerChoices`` django-enum_ provides
:class:`~django_enum.choices.TextChoices`, :class:`~django_enum.choices.IntegerChoices`,
:class:`~django_enum.choices.FlagChoices` and :class:`~django_enum.choices.FloatChoices` types that
derive from :doc:`enum-properties:index` and Django's ``Choices``. So the above enumeration could also be
written:

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

.. note::

    To use these ``Choices`` extensions you will need to install :doc:`enum-properties:index` which is an
    optional dependency.

.. _forms:

Forms
#####

An ``EnumChoiceField`` type is provided that enables symmetric value resolution
and will automatically coerce any set value to the underlying enumeration type.
Django_'s ``ModelForms`` will use this form field type to represent
:class:`~django_enum.fields.EnumField` by default. For most scenarios this is sufficient. The
``EnumChoiceField`` can also be explicitly used. For example, using our
``TextChoicesExample`` from above - if ``color`` was declared with
`strict=False`, we could add additional choices to our form field like so:

.. code-block::

    from django_enum.forms import EnumChoiceField

    class TextChoicesExampleForm(ModelForm):

        color = EnumChoiceField(
            TextChoicesExample.Color,
            strict=False,
            choices=[
                ('P', 'Purple'),
                ('O', 'Orange'),
            ] + TextChoicesExample.Color.choices
        )

        class Meta:
            model = TextChoicesExample
            fields = '__all__'

    # when this form is rendered in a template it will include a selected
    # option for the value 'Y' that is not part of our Color enumeration.
    # since our field is not strict, we can set it to a value not in our
    # enum or choice tuple.
    form = TextChoicesExampleForm(
        instance=TextChoicesExample.objects.create(color='Y')
    )


.. code-block:: html

    <!-- The above will render the following options: -->
    <select>

        <!-- our extended choices -->
        <option value='P'>Purple</option>
        <option value='O'>Orange</option>

        <!-- choices from our enum -->
        <option value='R'>Red</option>
        <option value='G'>Green</option>
        <option value='B'>Blue</option>

        <!--
        non-strict fields that have data that is not a valid enum value and is
        not present in the form field's choices tuple will have that value
        rendered as the selected option.
        -->
        <option value='Y' selected>Y</option>
    </select>


.. _rest_framework:

Django Rest Framework
#####################

By default DRF_ ``ModelSerializer`` will use a ``ChoiceField`` to represent an
:class:`~django_enum.fields.EnumField`. This works great, but it will not accept symmetric enumeration
values. A serializer field :class:`~django_enum.fields.EnumField` is provided that will. The dependency
on DRF_ is optional so to use the provided serializer field you must install
DRF_:

.. code:: bash

    pip install djangorestframework

.. code-block::

    from django_enum.drf import EnumField
    from rest_framework import serializers

    class ExampleSerializer(serializers.Serializer):

        color = EnumField(TextChoicesExample.Color)

    ser = ExampleSerializer(data={'color': (1, 0, 0)})
    assert ser.is_valid()

The serializer :class:`~django_enum.fields.EnumField` accepts any arguments that ``ChoiceField``
does. It also accepts the ``strict`` parameter which behaves the same way as it does
on the model field.

.. _filtering:

Filtering
#########

As shown above, filtering by any value, enumeration type instance or symmetric
value works with Django_'s ORM. This is not natively true for automatically
generated ``FilterSets`` from django-filter_. Those filter sets will only be
filterable by direct enumeration value by default. An ``EnumFilter`` type is
provided to enable filtering by symmetric property values, but since the
dependency on django-filter_ is optional, you must first install it:

.. code:: bash

       pip install django-filter


.. code-block::

    from django_enum.filters import EnumFilter
    from django_filters.views import FilterView
    from django_filters import FilterSet

    class TextChoicesExampleFilterViewSet(FilterView):

        class TextChoicesExampleFilter(FilterSet):

            color = EnumFilter(TextChoicesExample.Color)

            class Meta:
                model = TextChoicesExample
                fields = '__all__'

        filterset_class = TextChoicesExampleFilter
        model = TextChoicesExample

    # now filtering by symmetric value in url parameters works:
    # e.g.:  /?color=FF0000

An ``EnumFilterSet`` type is also provided that uses ``EnumFilter`` for
:class:`~django_enum.fields.EnumField` by default. So the above is also equivalent to:

.. code-block::

    from django_enum.filters import FilterSet as EnumFilterSet
    from django_filters.views import FilterView

    class TextChoicesExampleFilterViewSet(FilterView):

        class TextChoicesExampleFilter(EnumFilterSet):
            class Meta:
                model = TextChoicesExample
                fields = '__all__'

        filterset_class = TextChoicesExampleFilter
        model = TextChoicesExample

.. _migrations:

Migrations
##########

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

Flag Enumerations
#################

Python supports `bit masks <https://en.wikipedia.org/wiki/Mask_(computing)>`_ through the
`Flag <https://docs.python.org/3/library/enum.html#enum.Flag>`_ extension to :class:`enum.Enum`.

These enumerations are fully supported and will render as multi select form fields
by default. For example:

.. code-block:: python

    from enum import IntFlag
    from django_enum import EnumField
    from django.db import models

    class MyModel(models.Model):

        class GNSSConstellation(IntFlag):

            GPS     = 2**1
            GLONASS = 2**2
            GALILEO = 2**3
            BEIDOU  = 2**4
            QZSS    = 2**5

        constellation = EnumField(GNSSConstellation)

    obj1 = MyModel.objects.create(
        constellation=(
            GNSSConstellation.GPS |
            GNSSConstellation.GLONASS |
            GNSSConstellation.GALILEO
        )
    )
    obj2 = MyModel.objects.create(constellation=GNSSConstellation.GPS)

    assert GNSSConstellation.GPS in obj1.constellation
    assert GNSSConstellation.GLONASS in obj1.constellation

**Two new field lookups are provided for flag enumerations:** ``has_any`` **and**
``has_all``.

.. _has_any:

has_any
-------

The ``has_any`` lookup will return any object that has at least one of the flags in the referenced
enumeration. For example:

.. code-block:: python

    # this will return both obj1 and obj2
    MyModel.objects.filter(
        constellation__has_any=GNSSConstellation.GPS | GNSSConstellation.QZSS
    )

.. _has_all:

has_all
-------

The ``has_all`` lookup will return any object that has at least all of the flags in the referenced
enumeration. For example:

.. code-block:: python

    # this will return only obj1
    MyModel.objects.filter(
        constellation__has_all=GNSSConstellation.GPS | GNSSConstellation.GLONASS
    )

**There are performance considerations when using a bit mask like a Flag enumeration instead of
multiple boolean columns.** See :ref:`flag performance <flag_performance>` for discussion and
benchmarks.

Flags with more than 64 bits
----------------------------

Flag enumerations of arbitrary size are supported, however if the enum has more
than 64 flags it will be stored as a :class:`django.db.models.BinaryField`. It is therefore
strongly recommended to keep your :class:`enum.Flag` enumerations at 64 bits or less.

.. warning::

    Support for extra large flag fields is experimental. ``has_any`` and ``has_all`` do not work.
    Most RDBMS systems do not support bitwise operations on binary fields. Future work may
    involve exploring support for this as a Postgres extension.


URLs
####

django-enum_ provides a :ref:`converter <urls>` that can be used to register enum url parameters
with the Django_ path resolver.

.. code-block:: python

    from enum import IntEnum

    from django.http import HttpResponse
    from django.urls import path

    from django_enum.urls import register_enum_converter


    class Enum1(IntEnum):
        A = 1
        B = 2

    register_enum_converter(Enum1)

    def enum_converter_view(request, enum):
        assert isinstance(enum, Enum1)
        return HttpResponse(status=200)


    # this will match paths /1/ and /2/
    urlpatterns = [
        path("<Enum1:enum>", register_enum_converter, name="enum1_view"),
    ]

By default the converter will use the value property of the enumeration to resolve the enumeration,
but this can be overridden by passing the `prop` parameter, so we could for example use the label
instead.
