"""
Specialized has_any and has_all query lookups for flag enumerations.
"""
from django.db.models.lookups import Exact


class HasAllFlagsLookup(Exact):  # pylint: disable=W0223
    """
    Extend Exact lookup to support lookup on has all flags. This lookup bitwise
    ANDs the column with the lookup value and checks that the result is equal
    to the lookup value.
    """

    lookup_name = 'has_all'

    def process_lhs(self, compiler, connection, lhs=None):
        lhs_sql, lhs_params = super().process_lhs(compiler, connection, lhs)
        rhs_sql, rhs_params = super().process_rhs(compiler, connection)
        return (' & ' if self.rhs else ' | ').join(
            (lhs_sql, rhs_sql)
        ), [*lhs_params, *rhs_params]

    def get_rhs_op(self, connection, rhs):
        return connection.operators['exact'] % rhs


class HasAnyFlagsLookup(HasAllFlagsLookup):  # pylint: disable=W0223
    """
    Extend Exact lookup to support lookup on has any flags. This bitwise ANDs
    the column with the lookup value and checks that the result is greater
    than zero.
    """

    lookup_name = 'has_any'

    def process_rhs(self, compiler, connection):
        rhs_sql, rhs_params = super().process_rhs(compiler, connection)
        rhs_params[0] = 0
        return rhs_sql, rhs_params

    def get_rhs_op(self, connection, rhs):
        return connection.operators['gt'] % rhs
