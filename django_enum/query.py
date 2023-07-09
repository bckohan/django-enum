from django.db.models.lookups import Exact


class HasAllFlagsLookup(Exact):

    lookup_name = 'has_all'

    def process_lhs(self, compiler, connection, lhs=None):
        lhs_sql, lhs_params = super(HasAllFlagsLookup, self).process_lhs(
            compiler,
            connection,
            lhs
        )
        op = ' & ' if self.rhs else ' | '
        rhs_sql, rhs_params = super(HasAllFlagsLookup, self).process_rhs(
            compiler,
            connection
        )
        return op.join((lhs_sql, rhs_sql)), [*lhs_params, *rhs_params]

    def get_rhs_op(self, connection, rhs_sql):
        return connection.operators['exact'] % rhs_sql


class HasAnyFlagsLookup(HasAllFlagsLookup):

    lookup_name = 'has_any'

    def process_rhs(self, compiler, connection, lhs=None):
        rhs_sql, rhs_params = super(HasAllFlagsLookup, self).process_rhs(
            compiler,
            connection
        )
        rhs_params[0] = 0
        return rhs_sql, rhs_params

    def get_rhs_op(self, connection, rhs_sql):
        return connection.operators['gt'] % rhs_sql
