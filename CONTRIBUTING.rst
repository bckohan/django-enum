.. _Poetry: https://python-poetry.org/
.. _Pylint: https://www.pylint.org/
.. _isort: https://pycqa.github.io/isort/
.. _mypy: http://mypy-lang.org/
.. _django-pytest: https://pytest-django.readthedocs.io/en/latest/
.. _pytest: https://docs.pytest.org/en/stable/
.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _readthedocs: https://readthedocs.org/
.. _me: https://github.com/bckohan

Contributing
############

Contributions are encouraged! Please use the issue page to submit feature
requests or bug reports. Issues with attached PRs will be given priority and
have a much higher likelihood of acceptance. Please also open an issue and
associate it with any submitted PRs. That said, the aim is to keep this library
as lightweight as possible. Only features with broad based use cases will be
considered.

We are actively seeking additional maintainers. If you're interested, please
contact me_.


Installation
------------

`django-enum` uses Poetry_ for environment, package and dependency
management:

.. code-block::

    poetry install -E all --with psycopg3

Documentation
-------------

`django-enum` documentation is generated using Sphinx_ with the
readthedocs_ theme. Any new feature PRs must provide updated documentation for
the features added. To build the docs run:

.. code-block::

    cd ./doc
    poetry run make html


Static Analysis
---------------

`django-enum` uses Pylint_ for python linting and mypy_ for static type
checking. Header imports are also standardized using isort_. Before any PR is
accepted the following must be run, and static analysis tools should not
produce any errors or warnings. Disabling certain errors or warnings where
justified is acceptable:

.. code-block::

    poetry run isort django_enum
    poetry run pylint django_enum
    poetry run mypy django_enum
    poetry run doc8 -q doc
    poetry check
    poetry run pip check
    poetry run safety check --full-report
    poetry run python -m readme_renderer ./README.rst


Running Tests
-------------

`django-enum` is setup to use pytest_ to run unit tests. All the tests are
housed in django_enum/tests/tests.py. Before a PR is accepted, all tests
must be passing and the code coverage must be at 100%. A small number of
exempted error handling branches are acceptable.

To run the full suite:

.. code-block::

    poetry run pytest

To run a single test, or group of tests in a class:

.. code-block::

    poetry run pytest <path_to_tests_file>::ClassName::FunctionName

For instance to run all tests in TestDjangoEnums, and then just the
test_properties_and_symmetry test you would do:

.. code-block::

    poetry run pytest django_enum/tests/tests.py::TestDjangoEnums
    poetry run pytest django_enum/tests/tests.py::TestDjangoEnums::test_properties_and_symmetry


RDBMS
-----

By default, the tests will run against postgresql so in order to run the tests
you will need to have a postgresql server running that is accessible to the
default postgres user with no password. The test suite can be run against any
RDBMS supported by Django. Just set the RDBMS environment variable to one
of:

  * postgres
  * sqlite
  * mysql
  * mariadb
  * oracle

The settings for each RDBMS can be found in django_enum/tests/settings.py. The
database settings can be altered via environment variables that are referenced
therein. The default settings are designed to work out of the box with the
official docker images for each RDBMS. Reference the github actions workflow
for an example of how to run the tests against each RDBMS using docker
containers.

Additional dependency groups will need to be installed for some RDBMS:

.. code-block::

    # for postgres using psycopg3
    poetry install -E all --with psycopg3

    # for postgres using psycopg2
    poetry install -E all --with psycopg2

    # for mysql or mariadb
    poetry install -E all --with mysql

    # for oracle
    poetry install -E all --with oracle
