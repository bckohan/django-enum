.. include:: ../refs.rst

.. _flags_bitfields:

=================
Flags (BitFields)
=================

There are many different Global Satellite Navigation Systems (GNSS) in operation today:

* `GPS <https://www.gps.gov>`_
* `GLONASS <https://glonass-iac.ru/en/about_glonass>`_
* `Galileo <https://www.esa.int/Applications/Satellite_navigation/Galileo>`_
* `BeiDou <http://en.beidou.gov.cn>`_
* `QZSS <https://qzss.go.jp/en>`_
* `IRNSS <https://www.isro.gov.in/IRNSS_Programme.html>`_

GNSS receivers may understand or be configured to track one or more of these systems. If we wanted
to build a data model of a GNSS receiver we would want to know which systems it can track. In
Django_ we might do this using a collection of boolean fields like this:

.. literalinclude:: ../../../tests/examples/models/gnss_vanilla.py

Which would allow us to check for receiver compatibility and filter requirements like this:

.. literalinclude:: ../../../tests/examples/gnss_vanilla_tutorial.py
    :lines: 3-

This works pretty well. As our data scales though the waste of using an entire column for each
boolean can add up. We can do better by using a single column as a bit field.

Python has a built-in :class:`enum.IntFlag` type that is used to represent bit fields. Bit fields
are useful for storing multiple boolean values in a single column. This is :ref:`much more space
efficient <performance>`. :class:`~django_enum.fields.EnumField` supports :class:`enum.IntFlag`
types out of the box. We could rewrite our GNSS receiver model like this:

.. literalinclude:: ../../../tests/examples/models/gnss.py
    :lines: 2-

And use it like this:

.. literalinclude:: ../../../tests/examples/gnss_tutorial.py
    :lines: 3-

The bit field model is much more compact and it does better in
:ref:`space efficiency and query performance <performance>`. We also get some additional lookup
types for :class:`~django_enum.fields.EnumField` that represent flags: :ref:`has_all` and
:ref:`has_any`.

The defined indexes are not necessarily used in our examples. They may be partially engaged for the
:ref:`has_all` lookups but not for :ref:`has_any`. Our flag lookups perform optimized bit mask
operations in the database. The bit field example will out perform the boolean example because it
consumes much less memory while doing table scans with particular improvements in hard to index
:ref:`has_any` queries.

