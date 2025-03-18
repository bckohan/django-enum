.. include:: ../refs.rst

.. _urls_howto:

==================
Use Enums in URLs
==================

django-enum_ provides a :ref:`converter <urls>` that can be used to register enum url parameters
with the Django_ path resolver.

.. literalinclude:: ../../../tests/examples/urls.py

By default the converter will use the value property of the enumeration to resolve the enumeration,
but this can be overridden by passing the `prop` parameter, so we could for example use the
name or label instead.

The reversals for the above paths would look like this:

.. literalinclude:: ../../../tests/examples/urls_howto.py
    :lines: 3-
