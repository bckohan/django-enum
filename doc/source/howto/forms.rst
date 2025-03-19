.. include:: ../refs.rst

.. _forms:

=========
Use Forms
=========

Two form classes are provided that enable the use of :class:`~django_enum.fields.EnumField` in
:class:`~django.forms.ModelForm` and :class:`~django.forms.Form` classes.
:class:`~django.forms.ModelForm` will use :class:`~django_enum.forms.EnumChoiceField` by default
to represent standard :class:`~django_enum.fields.EnumField` and
:class:`~django_enum.forms.EnumFlagField` to represent instances of
:class:`~django_enum.fields.FlagField`.

These form field types enable symmetric value resolution and will automatically coerce any set value
to the underlying enumeration type.

.. tip::

    See :class:`~django_enum.forms.ChoiceFieldMixin` for the list of parameters accepted by the
    form fields. These parameters mirror the parameters for :class:`~django_enum.fields.EnumField`.

Using :class:`~django_enum.forms.EnumChoiceField`
-------------------------------------------------

The form fields can be used directly on any form and we can use the configuration parameters to
alter behavior including, modifying the choices list or allowing non-strict values. For example,
using our :ref:`TextChoicesExample <enum_props>` - if ``color_ext`` was declared with
`strict=False`, we could add additional choices and set the form field to any string like so:

.. literalinclude:: ../../../tests/examples/choice_form_howto.py
    :lines: 2-

When we render this form using ``{{ form.as_p }}`` we get:

.. code-block:: html

    <form method="post">
        <p>
            <label for="id_color">Color:</label>
            <select name="color" id="id_color">
                <option value="R" selected>Red</option>
                <option value="G">Green</option>
                <option value="B">Blue</option>
            </select>
        </p>
        <p>
            <label for="id_color_ext">Color ext:</label>
            <select name="color_ext" id="id_color_ext">

                <!-- our extended choices -->
                <option value="P">Purple</option>
                <option value="O">Orange</option>

                <!-- choices from our enum -->
                <option value="R">Red</option>
                <option value="G">Green</option>
                <option value="B">Blue</option>

                <!--
                non-strict fields that have data that is not a valid enum value and is
                not present in the form field's choices tuple will have that value
                rendered as the selected option.
                -->
                <option value="Y" selected>Y</option>
            </select>
        </p>
        <button type="submit">Submit</button>
    </form>

``color_ext`` will validate any string value, but ``color`` will raise a
:exc:`~django.core.exceptions.ValidationError` if anything other than a valid ``Color`` enum is set.

Using :class:`~django_enum.forms.EnumFlagField`
-----------------------------------------------

.. todo::

    Add an example of using EnumFlagField
