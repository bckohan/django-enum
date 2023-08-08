.. include:: refs.rst

.. _performance:

==========================
Performance Considerations
==========================

Enums
=====

The cost to resolve a raw database value into an Enum_ type object is
non-zero but negligible and swamped by I/O in most scenarios.

An effort is made to characterize and monitor the performance penalty of
using ``EnumFields`` over a Django_ native field with choices and benchmark
tests ensure performance of future releases will remain stable or improve.

For the nominal case the deserialization penalty is roughly equivalent to a map
lookup, but may involve several exception stack unwinds in unusual non-strict
or eccentric enumeration cases.

.. note::

    The deserialization penalty can be eliminated by setting ``coerce`` to
    ``False``. This will require the developer to manually coerce the
    ``EnumField`` value to an Enum_ type object and is therefore usually
    not recommended - but may be appropriate if the dominate use case involves
    high volume serialization to a raw value instead.

Flags
=====

The typical flag-like data model is to use a separate boolean column for each
flag. **Using a flag** ``EnumField`` **out performs boolean columns in both
storage and query performance in all scenarios.**

.. note::

    For all of the query plots below, bitmasks and booleans values are assigned
    randomly with each of the values having a 50% chance of being set. The
    tables with boolean columns have exactly the same mask values as the tables
    with bitmasks. 10 queries are performed and averaged at each check point.
    Each query generates a different random mask value to query and each table
    both boolean and bitmask are queried with the same mask value.


No Indexing
-----------

When no indexes are used, the flag ``EnumField`` saves a significant amount
of space over the boolean column model. The following plot shows the storage
efficiency improvement over boolean columns as the number of flags increases
for each supported RDBMS. The oracle line shows extents which are allocated in
64kb chunks resulting in a larger step size.

.. figure:: plots/FlagSizeBenchmark.png
   :alt: Storage Efficiency improvement over boolean columns

   Storage efficiency improvement over boolean columns. The x-axis is the
   number of flags and the y-axis is the number of bytes saved per row by using
   a bitmask instead of a boolean column for each flag. The colored areas show
   the column type employed to store the bitmask given the number of flags.

For example, using PostgreSQL a table with a 32-flag column will save ~25 bytes
per row over an equivalent table with 32 boolean columns. *For a table with a
billion rows this equates to roughly 23 GB.*

Queries
~~~~~~~

When no indexes are used all three query types, `exact`, `has_all` and
`has_any` perform better when a bitmask is used. This is entirely because the
bitmask takes up less space and increases row throughput in memory as the RDBMS
does a full table scan:

.. figure:: plots/NoIndexQueryPerformance_postgres.png
   :alt: Query performance without indexes

   Query performance comparison without indexing. In this scenario, with a 16
   flag bitmask compared to 16 boolean columns, each of the three query types
   perform roughly 20-40% faster on PostgreSQL.


Indexed Exact Queries
---------------------

When an index is used, the flag ``EnumField`` marginally outperforms the
boolean column equivalent in both storage and query performance for exact match
queries. It is also much simpler to define. When using the boolean column
approach a multi-column index must be used. By default PostgreSQL is compiled
with a maximum multi-column index size of 32 columns. This means that masks
with more than 32 flags must be split into multiple multi-column indexes which
will further degrade performance compared to the equivalent flag ``EnumField``.

The multi-column limit on MySQL is only 16 columns.

.. todo::
    Plot a 33 flag bitmask as well.

.. figure:: plots/IndexedExactQueryPerformance_postgres.png
   :alt: Exact query performance without indexes

   Exact match query performance comparison with equivalent indexing on the
   flag and multi-column boolean approach.

Indexed All/Any Queries
-----------------------

Indexing for `has_all` or `has_any` queries requires a more complex indexing
approach than exact match queries.
