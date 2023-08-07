# pragma: no cover
import json
import os
import random
from functools import partial, reduce
from operator import and_, or_
from pathlib import Path
from time import perf_counter

from django.db import connection
from django.db.models import Q
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django_enum.tests.benchmark import enums as benchmark_enums
from django_enum.tests.benchmark import models as benchmark_models
from django_enum.tests.oracle_patch import patch_oracle
from django_enum.utils import get_set_bits
from tqdm import tqdm

try:
    import enum_properties
    ENUM_PROPERTIES_INSTALLED = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    ENUM_PROPERTIES_INSTALLED = False


BENCHMARK_FILE = Path(__file__).parent.parent.parent / 'benchmarks.json'

patch_oracle()


def get_table_size(cursor, table, total=True):
    if connection.vendor == 'postgresql':
        cursor.execute(
            f"SELECT pg_size_pretty(pg{'_total' if total else ''}"
            f"_relation_size('{table}'));"
        )
        size_bytes, scale = cursor.fetchone()[0].lower().split()
        size_bytes = float(size_bytes)
        if 'k' in scale:
            size_bytes *= 1024
        elif 'm' in scale:
            size_bytes *= 1024 * 1024
        elif 'g' in scale:
            size_bytes *= 1024 * 1024 * 1024

        return size_bytes
    elif connection.vendor == 'mysql':
        # weird table size explosion when #columns >= 24? see if OPTIMIZE
        # helps
        cursor.execute(f'OPTIMIZE TABLE {table}')
        cursor.fetchall()
        cursor.execute(
            f"SELECT ROUND((DATA_LENGTH "
            f"{'+ INDEX_LENGTH' if total else ''})) AS `bytes`"
            f"FROM information_schema.TABLES WHERE TABLE_NAME = '{table}';"
        )
        return cursor.fetchone()[0]
    elif connection.vendor == 'sqlite':
        cursor.execute(
            f'select sum(pgsize) as size from dbstat where name="{table}"'
        )
        return cursor.fetchone()[0]
    elif connection.vendor == 'oracle':
        # todo index total?
        cursor.execute(
            f"select sum(bytes) from user_extents where "
            f"segment_type='TABLE' and segment_name='{table.upper()}'"
        )
        ret = cursor.fetchone()

        if ret is None:
            import ipdb
            ipdb.set_trace()
        return ret[0]
    else:
        raise NotImplementedError(
            f'get_table_size not implemented for {connection.vendor}'
        )


def get_column_size(cursor, table, column):
    if connection.vendor == 'postgresql':
        cursor.execute(
            f"SELECT sum(pg_column_size({column})) FROM {table};"
        )
        return cursor.fetchone()[0]
    else:
        raise NotImplementedError(
            f'get_column_size not implemented for {connection.vendor}'
        )


class BulkCreateMixin:

    CHUNK_SIZE = 8196

    create_queue = {}

    def create(self, obj=None):
        if obj:
            self.create_queue.setdefault(obj.__class__, []).append(obj)
        for Model, queue in self.create_queue.items():
            if (
                (obj is None and queue) or
                len(queue) >= self.CHUNK_SIZE
            ):
                Model.objects.bulk_create(queue)
                queue.clear()




if ENUM_PROPERTIES_INSTALLED:

    from django_enum.tests.enum_prop.enums import (
        BigIntEnum,
        BigPosIntEnum,
        Constants,
        DJIntEnum,
        DJTextEnum,
        IntEnum,
        PosIntEnum,
        SmallIntEnum,
        SmallPosIntEnum,
        TextEnum,
    )
    from django_enum.tests.enum_prop.models import (
        EnumTester,
        NoCoercePerfCompare,
        PerfCompare,
        SingleEnumPerf,
        SingleFieldPerf,
        SingleNoCoercePerf,
    )


    @override_settings(DEBUG=False)
    class PerformanceTest(BulkCreateMixin, TestCase):
        """
        We intentionally test bulk operations performance because thats what
        we're most interested in with operations at this scale
        """

        CHUNK_SIZE = 2048
        COUNT = CHUNK_SIZE * 25
        MODEL_CLASS = EnumTester

        def test_benchmark(self):
            enum_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(
                    self.MODEL_CLASS(
                        small_pos_int=SmallPosIntEnum.VAL2,
                        small_int='Value -32768',
                        pos_int=2147483647,
                        int=-2147483648,
                        big_pos_int='Value 2147483648',
                        big_int='VAL2',
                        constant='φ',
                        text='V TWo',
                        dj_int_enum=3,
                        dj_text_enum=DJTextEnum.A,
                        non_strict_int=15,
                        non_strict_text='arbitrary',
                        no_coerce=SmallPosIntEnum.VAL2
                    )
                )
            self.create()
            enum_stop = perf_counter()

            delete_mark = self.MODEL_CLASS.objects.last().pk

            choice_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(
                    PerfCompare(
                        small_pos_int=2,
                        small_int=-32768,
                        pos_int=2147483647,
                        int=-2147483648,
                        big_pos_int=2147483648,
                        big_int=2,
                        constant=1.61803398874989484820458683436563811,
                        text='V22',
                        dj_int_enum=3,
                        dj_text_enum='A',
                        non_strict_int=15,
                        non_strict_text='arbitrary',
                        no_coerce=2
                    )
                )
            self.create()
            choice_stop = perf_counter()

            enum_direct_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(
                    self.MODEL_CLASS(
                        small_pos_int=SmallPosIntEnum.VAL2,
                        small_int=SmallIntEnum.VALn1,
                        pos_int=PosIntEnum.VAL3,
                        int=IntEnum.VALn1,
                        big_pos_int=BigPosIntEnum.VAL3,
                        big_int=BigIntEnum.VAL2,
                        constant=Constants.GOLDEN_RATIO,
                        text=TextEnum.VALUE2,
                        dj_int_enum=DJIntEnum.THREE,
                        dj_text_enum=DJTextEnum.A,
                        non_strict_int=15,
                        non_strict_text='arbitrary',
                        no_coerce=SmallPosIntEnum.VAL2
                    )
                )
            self.create()
            enum_direct_stop = perf_counter()
            self.MODEL_CLASS.objects.filter(pk__gt=delete_mark).delete()

            no_coerce_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(
                    NoCoercePerfCompare(
                        small_pos_int=2,
                        small_int=-32768,
                        pos_int=2147483647,
                        int=-2147483648,
                        big_pos_int=2147483648,
                        big_int=2,
                        constant=1.61803398874989484820458683436563811,
                        text='V22',
                        dj_int_enum=3,
                        dj_text_enum='A',
                        non_strict_int=15,
                        non_strict_text='arbitrary',
                        no_coerce=2
                    )
                )
            self.create()
            no_coerce_stop = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start
            enum_direct_time = enum_direct_stop - enum_direct_start
            no_coerce_time = no_coerce_stop - no_coerce_start
            # flag if performance degrades signficantly - running about 2x for big lookups
            print(
                f'(EnumTester) Bulk Create -> '
                f'EnumField: {enum_time} '
                f'EnumField (direct): {enum_direct_time} '
                f'EnumField (no coerce): {no_coerce_time} '
                f'ChoiceField: {choice_time}'
            )

            self.assertTrue((enum_time / choice_time) < 4)
            self.assertTrue((enum_direct_time / choice_time) < 3)
            self.assertTrue((no_coerce_time / choice_time) < 3)
            self.assertEqual(self.MODEL_CLASS.objects.count(), self.COUNT)
            self.assertEqual(PerfCompare.objects.count(), self.COUNT)
            self.assertEqual(NoCoercePerfCompare.objects.count(), self.COUNT)

            enum_start = perf_counter()
            for _ in self.MODEL_CLASS.objects.iterator(chunk_size=self.CHUNK_SIZE):
                continue
            enum_stop = perf_counter()

            choice_start = perf_counter()
            for _ in PerfCompare.objects.iterator(chunk_size=self.CHUNK_SIZE):
                continue
            choice_stop = perf_counter()

            no_coerce_start = perf_counter()
            for _ in NoCoercePerfCompare.objects.iterator(
                    chunk_size=self.CHUNK_SIZE):
                continue
            no_coerce_stop = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start
            no_coerce_time = no_coerce_stop - no_coerce_start
            self.assertTrue((enum_time / choice_time) < 7)
            self.assertTrue((no_coerce_time / choice_time) < 4)
            print(
                f'(EnumTester) Chunked Read -> '
                f'EnumField: {enum_time} '
                f'No Coercion: {no_coerce_time} '
                f'ChoiceField: {choice_time}'
            )

        def test_single_field_benchmark(self):

            enum_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(SingleEnumPerf(small_pos_int=0))
            self.create()
            enum_stop = perf_counter()

            choice_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(SingleFieldPerf(small_pos_int=0))
            self.create()
            choice_stop = perf_counter()

            no_coerce_start = perf_counter()
            for idx in range(0, self.COUNT):
                self.create(SingleNoCoercePerf(small_pos_int=0))
            self.create()
            no_coerce_end = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start
            no_coerce_time = no_coerce_end - no_coerce_start

            print(
                f'(Single Field) Bulk Creation -> '
                f'EnumField: {enum_time} '
                f'No Coercion: {no_coerce_time} '
                f'ChoiceField: {choice_time}'
            )
            # Enum tends to be about ~12% slower
            self.assertTrue((enum_time / choice_time) < 1.8)
            self.assertTrue((no_coerce_time / choice_time) < 1.7)

            enum_start = perf_counter()
            for _ in SingleEnumPerf.objects.iterator(chunk_size=self.CHUNK_SIZE):
                continue
            enum_stop = perf_counter()

            choice_start = perf_counter()
            for _ in SingleFieldPerf.objects.iterator(chunk_size=self.CHUNK_SIZE):
                continue
            choice_stop = perf_counter()

            no_coerce_start = perf_counter()
            for _ in SingleNoCoercePerf.objects.iterator(
                    chunk_size=self.CHUNK_SIZE):
                continue
            no_coerce_end = perf_counter()

            enum_time = enum_stop - enum_start
            choice_time = choice_stop - choice_start
            no_coerce_time = no_coerce_end - no_coerce_start

            print(
                f'(Single Field) Chunked Read -> '
                f'EnumField: {enum_time} '
                f'No Coercion: {no_coerce_time} '
                f'ChoiceField: {choice_time}'
            )
            # tends to be about 1.8x slower
            self.assertTrue((enum_time / choice_time) < 2.5)
            self.assertTrue((no_coerce_time / choice_time) < 2)


@override_settings(
    DEBUG=False,
    INSTALLED_APPS = [
        'django_enum.tests.benchmark',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.admin',
    ]
)
class FlagBenchmarks(BulkCreateMixin, TestCase):

    COUNT = 1000

    FLAG_MODELS = [
        mdl for name, mdl in benchmark_models.__dict__.items()
        if hasattr(mdl, 'FLAG')
    ]
    BOOL_MODELS = [
        mdl for name, mdl in benchmark_models.__dict__.items()
        if hasattr(mdl, 'BOOL')
    ]

    def setUp(self):

        for FlagModel, BoolModel in zip(self.FLAG_MODELS, self.BOOL_MODELS):
            for idx in range(0, self.COUNT):
                assert FlagModel.num_flags == BoolModel.num_flags
                mask = random.getrandbits(FlagModel.num_flags)
                self.create(FlagModel(flags=mask))
                self.create(BoolModel(**{
                    f'flg_{flg}': bool(mask & (1 << flg) != 0)
                    for flg in range(0, BoolModel.num_flags)
                }))

        self.create()

    def test_size_benchmark(self):

        flag_totals = []
        flag_table = []
        flag_column = []

        bool_totals = []
        bool_table = []
        bool_column = []

        with connection.cursor() as cursor:
            for idx, (FlagModel, BoolModel) in enumerate(zip(self.FLAG_MODELS, self.BOOL_MODELS)):
                assert FlagModel.num_flags == BoolModel.num_flags == (idx + 1)

                flag_totals.append(get_table_size(cursor, FlagModel._meta.db_table, total=True))
                bool_totals.append(get_table_size(cursor, BoolModel._meta.db_table, total=True))

                flag_table.append(get_table_size(cursor, FlagModel._meta.db_table, total=False))
                bool_table.append(get_table_size(cursor, BoolModel._meta.db_table, total=False))

                if connection.vendor in ['postgresql']:
                    flag_column.append(
                        get_column_size(
                            cursor,
                            FlagModel._meta.db_table,
                            FlagModel._meta.get_field('flags').column)
                    )

                    bool_column.append(sum([
                        get_column_size(
                            cursor,
                            BoolModel._meta.db_table,
                            BoolModel._meta.get_field(f'flg_{flg}').column
                        ) for flg in range(0, BoolModel.num_flags)
                    ]))

        data = {}
        if BENCHMARK_FILE.is_file():
            with open(BENCHMARK_FILE, 'r') as bf:
                try:
                    data = json.load(bf)
                except json.JSONDecodeError:
                    pass

        with open(BENCHMARK_FILE, 'w') as bf:
            sizes = data.setdefault(
                'size', {}
            ).setdefault(
                os.environ.get('RDBMS', connection.vendor), {
                    'flags': {},
                    'bools': {}
                }
            )
            sizes['flags']['total'] = flag_totals
            sizes['flags']['table'] = flag_table
            sizes['flags']['column'] = flag_column
            sizes['bools']['total'] = bool_totals
            sizes['bools']['table'] = bool_table
            sizes['bools']['column'] = bool_column

            data['size'].setdefault('count', self.COUNT)
            assert self.COUNT == data['size']['count']

            bf.write(json.dumps(data, indent=4))

    def test_query_performance(self):

        has_any_flag_count = {}
        has_all_flag_count = {}
        has_any_flag_load = {}
        has_all_flag_load = {}

        has_any_bool_count = {}
        has_all_bool_count = {}
        has_any_bool_load = {}
        has_all_bool_load = {}

        with connection.cursor() as cursor:
            for FlagModel, BoolModel in zip(self.FLAG_MODELS, self.BOOL_MODELS):
                assert FlagModel.num_flags == BoolModel.num_flags

                mask = random.getrandbits(FlagModel.num_flags)
                if not mask:
                    mask = 1
                mask_en = FlagModel._meta.get_field('flags').enum(mask)

                flag_any_q = FlagModel.objects.filter(flags__has_any=mask_en)
                flag_all_q = FlagModel.objects.filter(flags__has_all=mask_en)

                bool_q = [
                    Q(**{f'flg_{flg}': bool(mask & (1 << flg) != 0)})
                    for flg in range(0, BoolModel.num_flags)
                    if bool(mask & (1 << flg) != 0)
                ]
                bool_any_q = (
                    BoolModel.objects.filter(reduce(or_, bool_q))
                    if bool_q else BoolModel.objects.none()
                )

                bool_all_q = (
                    BoolModel.objects.filter(reduce(and_, bool_q))
                    if bool_q else BoolModel.objects.none()
                )

                start = perf_counter()
                flag_any_count = flag_any_q.count()
                has_any_flag_count[FlagModel.num_flags] = perf_counter() - start

                start = perf_counter()
                bool_any_count = bool_any_q.count()
                has_any_bool_count[BoolModel.num_flags] = perf_counter() - start

                try:
                    # make sure our queries are equivalent
                    self.assertEqual(flag_any_count, bool_any_count)
                except AssertionError:
                    import ipdb
                    ipdb.set_trace()

                start = perf_counter()
                flag_all_count = flag_all_q.count()
                has_all_flag_count[FlagModel.num_flags] = perf_counter() - start

                start = perf_counter()
                bool_all_count = bool_all_q.count()
                has_all_bool_count[BoolModel.num_flags] = perf_counter() - start

                # make sure our queries are equivalent
                self.assertEqual(flag_all_count, bool_all_count)

                start = perf_counter()
                flag_any_list = list(flag_any_q.all())
                has_any_flag_load[FlagModel.num_flags] = perf_counter() - start

                start = perf_counter()
                bool_any_list = list(bool_any_q.all())
                has_any_bool_load[BoolModel.num_flags] = perf_counter() - start

                # make sure our queries are equivalent
                self.assertEqual(len(flag_any_list), len(bool_any_list))

                start = perf_counter()
                flag_all_list = list(flag_all_q.all())
                has_all_flag_load[FlagModel.num_flags] = perf_counter() - start

                start = perf_counter()
                bool_all_list = list(bool_all_q.all())
                has_all_bool_load[BoolModel.num_flags] = perf_counter() - start

                # make sure our queries are equivalent
                self.assertEqual(len(flag_all_list), len(bool_all_list))

        num_flags = sorted(has_any_flag_count.keys())

        has_any_count_diff = [
            has_any_bool_count[flg] - has_any_flag_count[flg]
            for flg in num_flags
        ]
        has_all_count_diff = [
            has_all_bool_count[flg] - has_all_flag_count[flg]
            for flg in num_flags
        ]

        has_any_load_diff = [
            has_any_bool_load[flg] - has_any_flag_load[flg]
            for flg in num_flags
        ]
        has_all_load_diff = [
            has_all_bool_load[flg] - has_all_flag_load[flg]
            for flg in num_flags
        ]

        # print(has_any_count_diff)
        # print('--------------------------------')
        # print(has_all_count_diff)
        # print('--------------------------------')
        # print(has_any_load_diff)
        # print('--------------------------------')
        # print(has_all_load_diff)

        has_any_count_tpl = [
            (has_any_bool_count[flg],  has_any_flag_count[flg])
            for flg in num_flags
        ]
        has_all_count_tpl = [
            (has_all_bool_count[flg],  has_all_flag_count[flg])
            for flg in num_flags
        ]

        has_any_load_tpl = [
            (has_any_bool_load[flg], has_any_flag_load[flg])
            for flg in num_flags
        ]
        has_all_load_tpl = [
            (has_all_bool_load[flg], has_all_flag_load[flg])
            for flg in num_flags
        ]

        print('------------ has_any_cnt ----------------')
        print(has_any_count_tpl)
        print('------------ has_all_cnt ----------------')
        print(has_all_count_tpl)
        print('------------ has_any_load ---------------')
        print(has_any_load_tpl)
        print('------------ has_all_load ---------------')
        print(has_all_load_tpl)


class FlagIndexTests(BulkCreateMixin, TestCase):

    CHECK_POINTS = [
        *(int(10**i) for i in range(1, 7)),
        *(int(i * ((10**7) / 5)) for i in range(1, 6)),
        *(int(i * ((10**8) / 5)) for i in range(1, 6)),
        #*(int(i * ((10**9) / 5)) for i in range(1, 6))
    ]

    NUM_FLAGS = 16

    FlagModel = getattr(benchmark_models, f'FlagTester{NUM_FLAGS-1:03d}')
    EnumClass = FlagModel._meta.get_field('flags').enum
    BoolModel = getattr(benchmark_models, f'BoolTester{NUM_FLAGS-1:03d}')

    flag_indexes = []
    bool_indexes = []

    @property
    def num_flags(self):
        return self.NUM_FLAGS

    def setUp(self):
        self.FlagModel.objects.all().delete()
        self.BoolModel.objects.all().delete()

    def tearDown(self) -> None:
        self.FlagModel.objects.all().delete()
        self.BoolModel.objects.all().delete()

    def create_rows(self, total, pbar):
        """
        Create a bunch of rows with random flags set, until the total number
        of rows is equal to `total`.
        """
        f_cnt = self.FlagModel.objects.count()
        b_cnt = self.BoolModel.objects.count()
        assert f_cnt == b_cnt

        for idx in range(f_cnt, total+1):
            mask = random.getrandbits(self.FlagModel.num_flags)
            set_flags = get_set_bits(mask)
            self.create(self.FlagModel(flags=mask))
            self.create(self.BoolModel(**{
                f'flg_{flg}': True for flg in set_flags
            }))
            pbar.update(n=1)

        self.create()

    def do_flag_query(self, masks):

        flg_all = []
        flg_any = []
        flg_exact = []

        flg_all_time = 0
        flg_any_time = 0
        flg_exact_time = 0

        for mask in masks:

            # dont change query order

            start = perf_counter()
            flg_all.append(self.FlagModel.objects.filter(flags__has_all=mask).count())
            flg_all_time += perf_counter() - start

            start = perf_counter()
            flg_any.append(self.FlagModel.objects.filter(flags__has_any=mask).count())
            flg_any_time += perf_counter() - start

            start = perf_counter()
            flg_exact.append(self.FlagModel.objects.filter(flags=mask).count())
            flg_exact_time += perf_counter() - start

        with connection.cursor() as cursor:
            table_size = get_table_size(
                cursor, self.FlagModel._meta.db_table, total=True
            )

        return (
            flg_all_time / len(masks),
            flg_any_time / len(masks),
            flg_exact_time / len(masks),
            flg_all, flg_any, flg_exact,
            table_size
        )

    def do_bool_query(self, masks, use_all=False):

        bool_all = []
        bool_any = []
        bool_exact = []

        bool_all_time = 0
        bool_any_time = 0
        bool_exact_time = 0

        for mask in masks:
            set_bits = get_set_bits(mask)

            bq = [Q(**{f'flg_{flg}': True}) for flg in set_bits]
            bq_all = reduce(and_, bq)
            bq_any = reduce(or_, bq)

            if use_all:
                def get_all_q(set_bits):
                    return [
                        Q(**{f'flg_{flg}': True})
                        if flg in set_bits else
                        Q(**{f'flg_{flg}__in': [True, False]})
                        for flg in range(self.num_flags)
                    ]

                bq_all = reduce(and_, get_all_q(set_bits))

                # todo there is not a better way to formulate a has_any query
                #  that will use the index ??

                # bq_any = reduce(
                #     or_,
                #     [reduce(and_, get_all_q([bit])) for bit in set_bits]
                # )

            exact_q = reduce(
                and_,
                [
                    Q(**{f'flg_{flg}': flg in set_bits})
                    for flg in range(self.num_flags)
                ]
            )

            # dont change query order
            start = perf_counter()
            bool_all.append(self.BoolModel.objects.filter(bq_all).count())
            bool_all_time += perf_counter() - start

            start = perf_counter()
            if isinstance(bq_any, str):
                with connection.cursor() as cursor:
                    cursor.execute(bq_any)
                    bool_any.append(int(cursor.fetchall()[0][0]))
            else:
                bool_any.append(self.BoolModel.objects.filter(bq_any).count())
            bool_any_time += perf_counter() - start

            start = perf_counter()
            bool_exact.append(self.BoolModel.objects.filter(exact_q).count())
            bool_exact_time += perf_counter() - start

        with connection.cursor() as cursor:
            table_size = get_table_size(
                cursor, self.BoolModel._meta.db_table, total=True
            )

        return (
            bool_all_time / len(masks),
            bool_any_time / len(masks),
            bool_exact_time / len(masks),
            bool_all, bool_any, bool_exact,
            table_size
        )

    def test_indexes(self):

        vendor = os.environ.get('RDBMS', connection.vendor)

        data = {}
        if BENCHMARK_FILE.is_file():
            with open(BENCHMARK_FILE, 'r') as bf:
                try:
                    data = json.load(bf)
                except json.JSONDecodeError:
                    pass
        data.setdefault('queries', {}).setdefault(vendor, {})

        def no_index():
            pass

        queries = {}
        with tqdm(total=self.CHECK_POINTS[-1]) as pbar:
            for check_point in self.CHECK_POINTS:
                self.create_rows(check_point, pbar)

                # keep search value at this point constant across methods
                masks = [
                    self.EnumClass(random.getrandbits(self.num_flags))
                    for _ in range(10)
                ]
                all_mask_counts = [[] for _ in range(len(masks))]
                any_mask_counts = [[] for _ in range(len(masks))]
                exact_mask_counts = [[] for _ in range(len(masks))]
                for index, name, query in [
                    (no_index, '[FLAG] No Index', self.do_flag_query),
                    (self.flag_single_index, '[FLAG] Single Index', self.do_flag_query),
                    (no_index, '[BOOL] No Index', self.do_bool_query),
                    (self.bool_column_indexes, '[BOOL] Col Index', self.do_bool_query),
                    (self.bool_multi_column_indexes, '[BOOL] MultiCol Index', partial(self.do_bool_query, use_all=True)),
                    #(self.postgres_gin, '[BOOL] GIN', self.do_bool_query),
                ]:
                    index()

                    with CaptureQueriesContext(connection) as ctx:
                        (
                            all_time, any_time, exact_time,
                            all_cnts, any_cnts, exact_cnts,
                            table_size
                        ) = query(masks)
                        queries[f'{name} has_all'] = ctx.captured_queries[0]['sql']
                        queries[f'{name} has_any'] = ctx.captured_queries[1]['sql']
                        queries[f'{name} has_exact'] = ctx.captured_queries[2]['sql']

                    for idx, (all_cnt, any_cnt, exact_cnt) in enumerate(
                        zip(all_cnts, any_cnts, exact_cnts)
                    ):
                        all_mask_counts[idx].append(all_cnt)
                        any_mask_counts[idx].append(any_cnt)
                        exact_mask_counts[idx].append(exact_cnt)

                    self.drop_indexes()

                    index_benchmarks = data['queries'][vendor].setdefault(
                        name, {}
                    ).setdefault(self.num_flags, {})
                    index_benchmarks[check_point] = {
                        'all_time': all_time,
                        'any_time': any_time,
                        'exact_time': exact_time,
                        'table_size': table_size
                    }

                # sanity checks
                for all_counts, any_counts, exact_counts in zip(
                        all_mask_counts,
                        any_mask_counts,
                        exact_mask_counts
                ):
                    try:
                        self.assertEqual(max(all_counts), min(all_counts))
                        self.assertEqual(max(any_counts), min(any_counts))
                        self.assertEqual(max(exact_counts), min(exact_counts))
                        self.assertGreater(any_counts[0], 0)
                        self.assertGreater(any_counts[0], all_counts[0])
                        self.assertTrue(all_counts[0] >= exact_counts[0])
                    except AssertionError:
                        import ipdb
                        ipdb.set_trace()
                        raise

        with open(BENCHMARK_FILE, 'w') as bf:
            bf.write(json.dumps(data, indent=4))

    def drop_indexes(self):

        def drop_index(table, index):
            if connection.vendor in ['oracle', 'postgresql', 'sqlite']:
                cursor.execute(f'DROP INDEX {index}')
            elif connection.vendor == 'mysql':
                cursor.execute(f'ALTER TABLE {table} DROP INDEX {index}')
            else:
                raise NotImplementedError(
                    f'Drop index for vendor {connection.vendor} not '
                    f'implemented!'
                )

        with connection.cursor() as cursor:

            for idx in self.flag_indexes:
                drop_index(self.FlagModel._meta.db_table, idx)
            self.flag_indexes.clear()

            for idx in self.bool_indexes:
                drop_index(self.BoolModel._meta.db_table, idx)
            self.bool_indexes.clear()

    def postgres_gin(self):

        with connection.cursor() as cursor:
            """
            Need a GIN operator for boolean columns
            """
            columns = ','.join([f'flg_{idx}' for idx in range(self.num_flags)])
            cursor.execute(
                f'CREATE INDEX bool_gin_index ON {self.BoolModel._meta.db_table} USING gin({columns})'
            )
            self.bool_indexes.append('bool_gin_index')

    def bool_column_indexes(self):

        with connection.cursor() as cursor:

            for idx in range(self.num_flags):
                idx_name = f'bool_{idx}'
                cursor.execute(f'CREATE INDEX {idx_name} ON {self.BoolModel._meta.db_table} (flg_{idx})')
                self.bool_indexes.append(idx_name)

    def bool_multi_column_indexes(self):

        with connection.cursor() as cursor:

            idx_name = 'bool_multi'
            columns = ','.join([f'flg_{idx}' for idx in range(self.num_flags)])
            cursor.execute(
                f'CREATE INDEX {idx_name} ON '
                f'{self.BoolModel._meta.db_table} ({columns})'
            )
            self.bool_indexes.append(idx_name)

    def flag_single_index(self):

        with connection.cursor() as cursor:
            idx_name = f'flag_idx'
            cursor.execute(f'CREATE INDEX {idx_name} ON {self.FlagModel._meta.db_table} (flags)')
            self.flag_indexes.append(idx_name)
