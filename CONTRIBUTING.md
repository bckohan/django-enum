# Contributing

Contributions are encouraged! Please use the issue page to submit feature requests or bug reports. Issues with attached PRs will be given priority and have a much higher likelihood of acceptance. Please also open an issue and associate it with any submitted PRs. That said, the aim is to keep this library as lightweight as possible. Only features with broad based use cases will be considered.

We are actively seeking additional maintainers. If you're interested, please contact [me](https://github.com/bckohan).


## Installation

`django-enum` uses [Poetry](https://python-poetry.org/) for environment, package and dependency management:

```console
    poetry install -E all --with psycopg3
```

## Documentation

`django-enum` documentation is generated using [Sphinx](https://www.sphinx-doc.org). Any new feature PRs must provide updated documentation for the features added. To build the docs run:

```console
    cd ./doc
    poetry run make html
```

## Static Analysis

`django-enum` uses [ruff](https://docs.astral.sh/ruff) for python linting and formatting. [mypy](http://mypy-lang.org) is used for static type checking. Before any PR is accepted the following must be run, and static analysis tools should not produce any errors or warnings. Disabling certain errors or warnings where justified is acceptable:

```console
    ./check.sh
```


## Running Tests

`django-enum` uses [pytest](https://docs.pytest.org/) to define and run tests. All the tests are housed in tests/tests.py. Before a PR is accepted, all tests must be passing and the code coverage must be at 100%. A small number of exempted error handling branches are acceptable.

To run the full suite:

```console
    poetry run pytest
```

To run a single test, or group of tests in a class:

```console
    poetry run pytest <path_to_tests_file>::ClassName::FunctionName
```

For instance to run all tests in TestDjangoEnums, and then just the
test_properties_and_symmetry test you would do:

```console
    poetry run pytest tests/tests.py::TestDjangoEnums
    poetry run pytest tests/tests.py::TestDjangoEnums::test_properties_and_symmetry
```

## RDBMS

By default, the tests will run against postgresql so in order to run the tests you will need to have a postgresql server running that is accessible to the default postgres user with no password. The test suite can be run against any RDBMS supported by Django. Just set the RDBMS environment variable to one of:

  * postgres
  * sqlite
  * mysql
  * mariadb
  * oracle

The settings for each RDBMS can be found in tests/settings.py. The database settings can be altered via environment variables that are referenced therein. The default settings are designed to work out of the box with the official docker images for each RDBMS. Reference the github actions workflow for an example of how to run the tests against each RDBMS using docker containers.

Additional dependency groups will need to be installed for some RDBMS:

```console

    # for postgres using psycopg3
    poetry install -E all --with psycopg3

    # for postgres using psycopg2
    poetry install -E all --with psycopg2

    # for mysql or mariadb
    poetry install -E all --with mysql

    # for oracle
    poetry install -E all --with oracle
```

## Releases

The release workflow is triggered by tag creation. You must have git tag signing enabled.

```console
git tag -s vX.X.X -m "X.X.X Release"
git push origin vX.X.X
```