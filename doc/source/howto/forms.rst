.. include:: ../refs.rst

.. _forms:

=========
Use Forms
=========

django-enum_ provides custom :ref:`form fields <forms_ref>` and :ref:`widgets <widgets_ref>` that
make including :class:`~django_enum.fields.EnumField` and :class:`~django_enum.fields.FlagField`
fields on forms easy.

Using :class:`~django_enum.forms.EnumChoiceField`
-------------------------------------------------

By default Django's :class:`~django.forms.ModelForm` will use :class:`~django.forms.ChoiceField`
to represent :class:`~django_enum.fields.EnumField` fields. This works great, but if you're using
an enumeration with :ref:`symmetric properties <enum-properties:howto_symmetric_properties>` or
with custom :meth:`~enum.Enum._missing_` behavior that you would like the form to respect you must
use django-enum_'s :class:`~django_enum.forms.EnumChoiceField` instead. **This will happen by
default when using** :class:`~django.forms.ModelForm` **forms because field construction is
delegated to** :meth:`~django_enum.fields.EnumField.formfield`.

.. tip::

    See Django_'s documentation on :ref:`how to customize form fields <django:specifying-form-field-for-model-field>`
    for more detailed instructions on how to alter the default form behavior.

The form fields can be used directly on any form and we can use the configuration parameters to
alter behavior including, modifying the choices list or allowing non-strict values. For example,
using our :ref:`TextChoicesExample <enum_props>` - if ``color_ext`` was declared with
`strict=False`, we could add additional choices and set the form field to any string like so:

.. tabs::

   .. tab:: Python

    .. literalinclude:: ../../../tests/examples/choice_form_howto.py
        :lines: 2-

   .. tab:: HTML

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


   .. tab:: Rendered

      .. raw:: html

        <form onsubmit="return false;">
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

The default widgets used above derive from :class:`django.forms.Select`. We can also use radio
buttons instead by using :class:`django.forms.RadioSelect` and
:class:`django_enum.forms.NonStrictRadioSelect`:


.. tabs::

   .. tab:: Python

    .. literalinclude:: ../../../tests/examples/radio_form_howto.py
        :lines: 2-

   .. tab:: HTML

    When we render this form using ``{{ form.as_p }}`` we get:

    .. code-block:: html

        <form method="post">
            <p>
                <label for="id_color_0">Color:</label>
            </p>
            <ul id="id_color">
                <li>
                    <label for="id_color_0">
                        <input type="radio" name="color" value="R" required="" id="id_color_0" checked="">
                        Red
                    </label>
                </li>
                <li>
                    <label for="id_color_1">
                        <input type="radio" name="color" value="G" required="" id="id_color_1">
                        Green
                    </label>
                </li>
                <li>
                    <label for="id_color_2">
                        <input type="radio" name="color" value="B" required="" id="id_color_2">
                        Blue
                    </label>
                </li>
            </ul>
            <p></p>
            <p>
                <label for="id_color_ext_0">Color ext:</label>
            </p>
            <ul id="id_color_ext">
                <li>
                    <label for="id_color_ext_0">
                        <input type="radio" name="color_ext" value="P" required="" id="id_color_ext_0">
                        Purple
                    </label>
                </li>
                <li>
                    <label for="id_color_ext_1">
                        <input type="radio" name="color_ext" value="O" required="" id="id_color_ext_1">
                        Orange
                    </label>
                </li>
                <li>
                    <label for="id_color_ext_2">
                        <input type="radio" name="color_ext" value="R" required="" id="id_color_ext_2">
                        Red
                    </label>
                </li>
                <li>
                    <label for="id_color_ext_3">
                        <input type="radio" name="color_ext" value="G" required="" id="id_color_ext_3">
                        Green
                    </label>
                </li>
                <li>
                    <label for="id_color_ext_4">
                        <input type="radio" name="color_ext" value="B" required="" id="id_color_ext_4">
                        Blue
                    </label>
                </li>
                <li>
                    <label for="id_color_ext_5">
                        <input type="radio" name="color_ext" value="Y" required="" id="id_color_ext_5" checked="">
                        Y
                    </label>
                </li>
            </ul>
            <p></p>
            <button type="submit">Submit</button>
        </form>


   .. tab:: Rendered

      .. raw:: html

        <form onsubmit="return false;">
            <p>
                <label for="id_color_0">Color:</label>
            </p>
            <ul id="id_color">
                <li>
                    <label for="id_color_0">
                        <input type="radio" name="color" value="R" required="" id="id_color_0" checked="">
                        Red
                    </label>
                </li>
                <li>
                    <label for="id_color_1">
                        <input type="radio" name="color" value="G" required="" id="id_color_1">
                        Green
                    </label>
                </li>
                <li>
                    <label for="id_color_2">
                        <input type="radio" name="color" value="B" required="" id="id_color_2">
                        Blue
                    </label>
                </li>
            </ul>
            <p></p>
            <p>
                <label for="id_color_ext_0">Color ext:</label>
            </p>
            <ul id="id_color_ext">
                <li>
                    <label for="id_color_ext_0">
                        <input type="radio" name="color_ext" value="P" required="" id="id_color_ext_0">
                        Purple
                    </label>
                </li>
                <li>
                    <label for="id_color_ext_1">
                        <input type="radio" name="color_ext" value="O" required="" id="id_color_ext_1">
                        Orange
                    </label>
                </li>
                <li>
                    <label for="id_color_ext_2">
                        <input type="radio" name="color_ext" value="R" required="" id="id_color_ext_2">
                        Red
                    </label>
                </li>
                <li>
                    <label for="id_color_ext_3">
                        <input type="radio" name="color_ext" value="G" required="" id="id_color_ext_3">
                        Green
                    </label>
                </li>
                <li>
                    <label for="id_color_ext_4">
                        <input type="radio" name="color_ext" value="B" required="" id="id_color_ext_4">
                        Blue
                    </label>
                </li>
                <li>
                    <label for="id_color_ext_5">
                        <input type="radio" name="color_ext" value="Y" required="" id="id_color_ext_5" checked="">
                        Y
                    </label>
                </li>
            </ul>
            <p></p>
            <button type="submit">Submit</button>
        </form>

.. tip::

    Have a look at :ref:`widgets <widgets_ref>` to see all the widgets that are available.

Using :class:`~django_enum.forms.EnumFlagField`
-----------------------------------------------

:class:`~django_enum.fields.FlagField` fields must be rendered with
:class:`django_enum.forms.EnumFlagField` on forms to work properly. This will happen automatically
for :class:`django.forms.ModelForm` because it delegates the field creation to
:meth:`~django_enum.fields.FlagField.formfield`. This form field type accepts incoming lists of
flags and combines them into composite flag types. The cleaned value is a single flag instance
value, but the interface to world is :func:`decomposed <django_enum.utils.decompose>`.

.. tabs::

    This example uses the ``Permissions`` enum from :ref:`the flags howto <group_permissions_ex>`.

   .. tab:: Python

    .. literalinclude:: ../../../tests/examples/flag_form_howto.py
        :lines: 2-

   .. tab:: HTML

    When we render this form using ``{{ form.as_p }}`` we get:

    .. code-block:: html

        <form method="post">
            <p>
                <label for="id_permissions">Permissions:</label>
                <select name="permissions" required="" id="id_permissions" multiple="">
                    <option value="1" selected="">READ</option>
                    <option value="2">WRITE</option>
                    <option value="4" selected="">EXECUTE</option>
                </select>
            </p>
            <p>
                <label for="id_permissions_ext">Permissions ext:</label>
                <select name="permissions_ext" required="" id="id_permissions_ext" multiple="">
                    <option value="1" selected="">READ</option>
                    <option value="2" selected="">WRITE</option>
                    <option value="4">EXECUTE</option>

                    <!-- our non strict field allows bits outside of the enum to be set! -->
                    <option value="8" selected="">DELETE</option>
                </select>
            </p>
            <button type="submit">Submit</button>
        </form>


   .. tab:: Rendered

      .. raw:: html

        <form onsubmit="return false;">
            <p>
                <label for="id_permissions">Permissions:</label>
                <select name="permissions" required="" id="id_permissions" multiple="">
                    <option value="1" selected="">READ</option>
                    <option value="2">WRITE</option>
                    <option value="4" selected="">EXECUTE</option>
                </select>
            </p>
            <p>
                <label for="id_permissions_ext">Permissions ext:</label>
                <select name="permissions_ext" required="" id="id_permissions_ext" multiple="">
                    <option value="1" selected="">READ</option>
                    <option value="2" selected="">WRITE</option>
                    <option value="4">EXECUTE</option>
                    <option value="8" selected="">DELETE</option>
                </select>
            </p>
            <button type="submit">Submit</button>
        </form>


The default widgets used above derive from :class:`django.forms.SelectMultiple`. We can also use
checkboxes instead by using :class:`django_enum.forms.FlagCheckbox` and
:class:`django_enum.forms.NonStrictFlagCheckbox`:


.. tabs::

    This example uses the ``Permissions`` enum from :ref:`the flags howto <group_permissions_ex>`.

   .. tab:: Python

    .. literalinclude:: ../../../tests/examples/checkboxes_form_howto.py
        :lines: 2-

   .. tab:: HTML

    When we render this form using ``{{ form.as_p }}`` we get:

    .. code-block:: html

        <form method="post">
            <p>
                <label>Permissions:</label>
            </p>
            <ul id="id_permissions">
                <li>
                    <label for="id_permissions_0">
                        <input type="checkbox" name="permissions" value="1" id="id_permissions_0" checked="">
                        READ
                    </label>
                </li>
                <li>
                    <label for="id_permissions_1">
                        <input type="checkbox" name="permissions" value="2" id="id_permissions_1">
                        WRITE
                    </label>
                </li>
                <li>
                    <label for="id_permissions_2">
                        <input type="checkbox" name="permissions" value="4" id="id_permissions_2" checked="">
                        EXECUTE
                    </label>
                </li>
            </ul>
            <p></p>
            <p>
                <label>Permissions ext:</label>
            </p>
            <ul id="id_permissions_ext">
                <li>
                    <label for="id_permissions_ext_0">
                        <input type="checkbox" name="permissions_ext" value="1" id="id_permissions_ext_0" checked="">
                        READ
                    </label>
                </li>
                <li>
                    <label for="id_permissions_ext_1">
                        <input type="checkbox" name="permissions_ext" value="2" id="id_permissions_ext_1" checked="">
                        WRITE
                    </label>
                </li>
                <li>
                    <label for="id_permissions_ext_2">
                        <input type="checkbox" name="permissions_ext" value="4" id="id_permissions_ext_2">
                        EXECUTE
                    </label>
                </li>
                <li>
                    <label for="id_permissions_ext_3">
                        <input type="checkbox" name="permissions_ext" value="8" id="id_permissions_ext_3" checked="">
                        DELETE
                    </label>
                </li>
            </ul>
            <p></p>
            <button type="submit">Submit</button>
        </form>

   .. tab:: Rendered

      .. raw:: html

        <form onsubmit="return false;">
             <p>
                <label>Permissions:</label>
            </p>
            <ul id="id_permissions">
                <li>
                    <label for="id_permissions_0">
                        <input type="checkbox" name="permissions" value="1" id="id_permissions_0" checked="">
                        READ
                    </label>
                </li>
                <li>
                    <label for="id_permissions_1">
                        <input type="checkbox" name="permissions" value="2" id="id_permissions_1">
                        WRITE
                    </label>
                </li>
                <li>
                    <label for="id_permissions_2">
                        <input type="checkbox" name="permissions" value="4" id="id_permissions_2" checked="">
                        EXECUTE
                    </label>
                </li>
            </ul>
            <p></p>
            <p>
                <label>Permissions ext:</label>
            </p>
            <ul id="id_permissions_ext">
                <li>
                    <label for="id_permissions_ext_0">
                        <input type="checkbox" name="permissions_ext" value="1" id="id_permissions_ext_0" checked="">
                        READ
                    </label>
                </li>
                <li>
                    <label for="id_permissions_ext_1">
                        <input type="checkbox" name="permissions_ext" value="2" id="id_permissions_ext_1" checked="">
                        WRITE
                    </label>
                </li>
                <li>
                    <label for="id_permissions_ext_2">
                        <input type="checkbox" name="permissions_ext" value="4" id="id_permissions_ext_2">
                        EXECUTE
                    </label>
                </li>
                <li>
                    <label for="id_permissions_ext_3">
                        <input type="checkbox" name="permissions_ext" value="8" id="id_permissions_ext_3" checked="">
                        DELETE
                    </label>
                </li>
            </ul>
            <p></p>
            <button type="submit">Submit</button>
        </form>
