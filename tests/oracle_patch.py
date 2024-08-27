"""
monkey patch a fix to django oracle backend bug where DATE literals in
CheckConstraints are not recognized by Oracle without explicitly casting to
DATE. This patch allows eccentric tests to pass on Oracle - and is necessary
because those tests block the normal tests just based on how the test suite is
put together. So to do any significant testing on Oracle, this monkey patch is
necessary - remove when there is an upstream fix.
"""

from datetime import date, datetime, timedelta

from django.db.backends.oracle.schema import DatabaseSchemaEditor
from django.utils.duration import duration_iso_string


def patch_oracle():
    quote_value = DatabaseSchemaEditor.quote_value

    def quote_value_patched(self, value):
        if isinstance(value, date) and not isinstance(value, datetime):
            return "DATE '%s'" % value.isoformat()
        elif isinstance(value, timedelta):
            return "'%s'" % duration_iso_string(value)
        return quote_value(self, value)

    DatabaseSchemaEditor.quote_value = quote_value_patched
