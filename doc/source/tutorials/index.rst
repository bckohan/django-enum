.. include:: ../refs.rst

.. _tutorials:

=========
Tutorials
=========

Enumerations in Python can provide rich class based interfaces well suited to many use cases. We
present several real world scenarios here that demonstrate the capability of django-enum_ to get
your :class:`~django_enum.fields.EnumField` to do more work.

In the :ref:`properties <properties>` tutorial, we leverage :doc:`enum-properties:index` to
encapsulate more information onto our :class:`~enum.Enum` values so that any information needed in
different contexts is readily available without brittle mapping boilerplate. We also demonstrate
symmetric properties that are comparison equivalent to our enumeration values.

In the :ref:`flags <flags_bitfields>` tutorial, we demonstrate how to use :class:`enum.Flag`
enumerations to represent bitfields in a database. This is a common pattern for storing multiple
boolean values in a single column.

|

.. toctree::
   :maxdepth: 2
   :caption: Tutorials:

   properties
   flags
