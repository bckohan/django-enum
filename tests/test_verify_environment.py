import os
import sys
import django
from django.db import connection
import typing as t
from django.test import TestCase
import pytest


def get_postgresql_version() -> t.Tuple[int, ...]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        db, ver = version[0].split(" ")[:2]
        assert db == "PostgreSQL"
        return tuple(int(v) for v in ver.split(".")[:2] if v)


def get_mysql_version():
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()
        print("MySQL version:", version[0])


@pytest.mark.skipif(
    os.environ.get("GITHUB_ACTIONS", None) != "true",
    reason="This test is only for the CI environment.",
)
class TestEnvironment(TestCase):
    def test(self):
        # verify that the environment is set up correctly - this is used in CI to make
        # sure we're testing against the dependencies we think we are

        rdbms = os.environ["RDBMS"]
        expected_python = os.environ["TEST_PYTHON_VERSION"]
        expected_django = os.environ["TEST_DJANGO_VERSION"]
        expected_db_ver = os.environ.get("TEST_DATABASE_VERSION", None)
        expected_client = os.environ.get("TEST_DATABASE_CLIENT_VERSION", None)

        expected_python = tuple(int(v) for v in expected_python.split(".") if v)
        assert sys.version_info[: len(expected_python)] == expected_python, (
            f"Python Version Mismatch: {sys.version_info[: len(expected_python)]} != "
            f"{expected_python}"
        )

        try:
            expected_django = tuple(int(v) for v in expected_django.split(".") if v)
            assert django.VERSION[: len(expected_django)] == expected_django, (
                f"Django Version Mismatch: {django.VERSION[: len(expected_django)]} != "
                f"{expected_django}"
            )
        except ValueError:
            assert expected_django == django.__version__

        if expected_db_ver:
            if rdbms == "postgres":
                if expected_db_ver == "latest":
                    # todo
                    pass
                else:
                    expected_version = tuple(
                        int(v) for v in expected_db_ver.split(".") if v
                    )
                    assert (
                        expected_version
                        == get_postgresql_version()[: len(expected_version)]
                    )
                if expected_client == "psycopg3":
                    import psycopg

                    assert psycopg.__version__[0] == "3"
                else:
                    import psycopg2

                    assert psycopg2.__version__[0] == "2"
            elif rdbms == "mysql":
                pass
            elif rdbms == "mariadb":
                pass
            elif rdbms == "sqlite":
                pass
            elif rdbms == "oracle":
                pass
