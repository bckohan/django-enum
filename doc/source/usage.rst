.. include:: refs.rst

=====
Usage
=====

``EnumField`` inherits from the appropriate native Django_ field and sets the
correct choice tuple set based on the enumeration type. This means
``EnumFields`` are compatible with all modules, utilities and libraries that
fields defined with a choice tuple are. For example:

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

    # txt_enum fields, when populated from the db, or after full_clean will be
    # an instance of the TextEnum type:

    assert isinstance(MyModel.objects.first().txt_enum, MyModel.TextEnum)
    assert not isinstance(MyModel.objects.first().txt_choices, MyModel.TextEnum)

    # by default EnumFields are more strict, this is possible:
    MyModel.objects.create(
        txt_choices='AA'
    )

    # but this will throw a ValueError (unless strict=False)
    MyModel.objects.create(
        txt_enum='AA'
    )

    # and this will throw a ValidationError
    MyModel(txt_enum='AA').full_clean()

Any ``ModelForms``, DRF serializers and filters will behave the same way with
``txt_enum`` and ``txt_choices``. A few types are provided for deeper
integration with forms and django-filter_ but their usage is optional.
See :ref:`forms` and :ref:`filtering`.

Very rich enumeration fields that encapsulate much more functionality in a
simple declarative syntax are possible with ``EnumField``. See
:ref:`enum_props`.

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


.. _enum_props:

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


.. _forms:

Forms
#####

EnumFields will behave as normal model fields with choices when used in
Django_'s ModelForms. For most scenarios this is sufficient. An
``EnumChoiceField`` type is provided that enables symmetric value resolution
and will automatically coerce any set value to the underlying enumeration type.
For example, using our ``TextChoicesExample`` from above:

.. code-block::

    from django_enum import EnumChoiceField

    class TextChoicesExampleForm(ModelForm):
        color = EnumChoiceField(TextChoicesExample.Color)

        class Meta:
            model = TextChoicesExample
            fields = '__all__'

    # save by symmetric values
    form = TextChoicesExampleForm({'color': 'FF0000'})
    form.save()
    assert form.instance.color == TextChoicesExample.Color.RED

    # the form
    assert isinstance(form.instance.color, TextChoicesExample.Color)

``EnumChoiceField`` also provides extended functionality for non-strict
``EnumFields``. If our ``color`` field was declared with `strict=False`, we
would define our form like so:


.. code-block::

    from django_enum import EnumChoiceField

    class TextChoicesExampleForm(ModelForm):
        color = EnumChoiceField(TextChoicesExample.Color, strict=False)

        class Meta:
            model = TextChoicesExample
            fields = '__all__'

    # when this form is rendered in a template it will include a selected
    # option for the value 'Y' that is not part of our Color enumeration.
    form = TextChoicesExampleForm(
        instance=TextChoicesExample.objects.create(color='Y')
    )

.. code-block:: html

    <!-- The above will render the following options: -->
    <select>
        <option value='R'>Red</option>
        <option value='G'>Green</option>
        <option value='B'>Blue</option>

        <!-- this will not be present with the default field -->
        <option value='Y' selected>Y</option>
    </select>


.. _rest_framework:

Django Rest Framework
#####################

By default DRF_ ``ModelSerializer`` will use a ``ChoiceField`` to represent an
``EnumField``. This works great, but it will not accept symmetric enumeration
values. A serializer field ``EnumField`` is provided that will. The dependency
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

The serializer ``EnumField`` accepts any arguments that ``ChoiceField`` does.
It also accepts the ``strict`` parameter which behaves the same way as it does
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

    from django_enum import EnumFilter
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

An ``EnumFilterSet`` type is also provided that uses ``EnumFilter`` for ``EnumFields``
by default. So the above is also equivalent to:

.. code-block::

    from django_enum import FilterSet as EnumFilterSet
    from django_filters.views import FilterView

    class TextChoicesExampleFilterViewSet(FilterView):

        class TextChoicesExampleFilter(EnumFilterSet):
            class Meta:
                model = TextChoicesExample
                fields = '__all__'

        filterset_class = TextChoicesExampleFilter
        model = TextChoicesExample

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
non-zero. ``EnumFields`` may not be appropriate for use cases at the very edge
of critical performance targets, but for most scenarios the cost of using
``EnumFields`` is negligible.

An effort is made to characterize and monitor the performance penalty of
using ``EnumFields`` over a Django_ native field with choices and integration
tests ensure performance of future releases will not worsen.

.. note::

    The read performance penalty can be eliminated by setting ``coerce`` to
    ``False``.
